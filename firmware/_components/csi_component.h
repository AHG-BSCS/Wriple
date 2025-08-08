#ifndef ESP32_CSI_COMPONENT_H
#define ESP32_CSI_COMPONENT_H

#include <sstream>
#include "driver/gpio.h"
#include "driver/uart.h"
#include "lwip/sockets.h"

#include "rd03d_component.h"
#include "ld2420_component.h"

#define LED_GPIO_PIN GPIO_NUM_2
#define LED_PACKET_COUNT_BLINK 15

#define CSI_TAG "CSI"

SemaphoreHandle_t mutex = xSemaphoreCreateMutex();
TimerHandle_t led_timer;

static int total_packet_count = 0;
static int sock = -1;
static sockaddr_in client_addr;
static const char *target_ip = "192.168.11.222"; // IP address of the station

bool is_led_high = false;

void blink_led() {
    if (total_packet_count == 0) {
        is_led_high = !is_led_high;
        gpio_set_level(LED_GPIO_PIN, is_led_high);
        total_packet_count = LED_PACKET_COUNT_BLINK;
    }
}

void _wifi_csi_callback(void *ctx, wifi_csi_info_t *data) {
    // ESP_LOGI(CSI_TAG, "%d bytes", data[0].rx_ctrl.sig_len);
    // ESP_LOGI(CSI_TAG, "%d channel", data[0].rx_ctrl.cwb);
    // If from 40Mhz Channel with payload specific to station packet
    if (data[0].rx_ctrl.cwb == 0 && data[0].rx_ctrl.sig_len == 88) {
        xSemaphoreTake(mutex, portMAX_DELAY);
        
        std::stringstream ss;
        wifi_csi_info_t d = data[0];
        char mac[20] = {0};
        sprintf(mac, "%02X:%02X:%02X:%02X:%02X:%02X", d.mac[0], d.mac[1], d.mac[2], d.mac[3], d.mac[4], d.mac[5]);

        // (1) Metadata
        ss << d.rx_ctrl.timestamp << "," << d.rx_ctrl.rssi << "," << d.rx_ctrl.channel << "|";

        // (2) CSI
        for (int i = 0; i < data->len; i++) {
            ss << (int)data->buf[i];
            if (i < data->len - 1) ss << " ";
        }
        ss << "|";

        // (3) RD03D (3 targets × 4 fields each)
        ss << get_rd03d_data() << "|";

        // (4) LD2420 (20 doppler x 16 range gates)
        ss << get_ld2420_data() << "\n";

        // Send the CSI data to the station
        sendto(sock, ss.str().c_str(), strlen(ss.str().c_str()), 0, (struct sockaddr *)&client_addr, sizeof(client_addr));

        blink_led();
        total_packet_count--;
        xSemaphoreGive(mutex);
    }
    else if (data[0].rx_ctrl.sig_len == 86) {
        is_led_high = false;
        gpio_set_level(LED_GPIO_PIN, is_led_high);
        total_packet_count = 0;
    }
}

void csi_init() {
    wifi_csi_config_t csi_config;
    csi_config.lltf_en = 1;
    csi_config.htltf_en = 1;
    csi_config.stbc_htltf2_en = 1;
    csi_config.ltf_merge_en = 1;
    csi_config.channel_filter_en = 0;
    csi_config.manu_scale = 0;

    // Configure LED
    gpio_reset_pin(LED_GPIO_PIN);
    gpio_set_direction(LED_GPIO_PIN, GPIO_MODE_OUTPUT);

    ESP_ERROR_CHECK(esp_wifi_set_csi_config(&csi_config));
    ESP_ERROR_CHECK(esp_wifi_set_csi_rx_cb(&_wifi_csi_callback, NULL));
    ESP_ERROR_CHECK(esp_wifi_set_csi(1));

    client_addr.sin_family = AF_INET;
    client_addr.sin_port = htons(5000);
    client_addr.sin_addr.s_addr = inet_addr(target_ip);

    sock = socket(AF_INET, SOCK_DGRAM, 0);
}

#endif
