#ifndef ESP32_CSI_COMPONENT_H
#define ESP32_CSI_COMPONENT_H

#include <sstream>
#include "driver/gpio.h"
#include "driver/uart.h"
#include "lwip/sockets.h"

#include "rd03d_component.h"
#include "ld2420_component.h"

#define LED_GPIO_PIN GPIO_NUM_2

#define CSI_TAG "ESP32"

SemaphoreHandle_t mutex = xSemaphoreCreateMutex();
TimerHandle_t led_timer;

static bool connected = false;
static int total_packet_count = 0;

static int sock = -1;
static sockaddr_in client_addr;
static const uint8_t target_mac[6] = {0xE0, 0x2B, 0xE9, 0x95, 0xED, 0x68}; // MAC address of the station
static const char *target_ip = "192.168.4.2"; // IP address of the station

void led_timer_callback(TimerHandle_t xTimer) {
    if (connected && total_packet_count > 25) {
        gpio_set_level(LED_GPIO_PIN, 1);
        total_packet_count = 0;
    }
    else {
        gpio_set_level(LED_GPIO_PIN, 0);
    }
}

void _wifi_csi_callback(void *ctx, wifi_csi_info_t *data) {
    if ((memcmp(data->mac, target_mac, 6) == 0) &&
        (data[0].rx_ctrl.cwb == 1) &&       // 40Mhz Channel Bandwidth / 128 Subcarrier
        (data[0].rx_ctrl.sig_len == 89)) {  // Payload from station is 89 bytes long
        
        if (sock == -1) {
            ESP_LOGE(CSI_TAG, "Unable to create socket");
            vTaskDelete(NULL);
        }

        xSemaphoreTake(mutex, portMAX_DELAY);
        
        std::stringstream ss;
        wifi_csi_info_t d = data[0];
        std::string ld2420_rdmap_str = read_ld2420_debug_data();
        read_radar_data();
        char mac[20] = {0};
        sprintf(mac, "%02X:%02X:%02X:%02X:%02X:%02X", d.mac[0], d.mac[1], d.mac[2], d.mac[3], d.mac[4], d.mac[5]);

        // (1) Metadata
        ss << "(" << d.rx_ctrl.timestamp << "," << d.rx_ctrl.rssi << "," << d.rx_ctrl.channel << ") | ";

        // (2) CSI
        ss << "[";
        for (int i = 0; i < data->len; i++) {
            ss << (int)data->buf[i];
            if (i < data->len - 1) ss << " ";
        }
        ss << "] | ";

        // (3) RD03D (3 targets × 4 fields each)
        ss << "("
        << get_target1_x() << "," << get_target1_y() << "," << get_target1_speed() << "," << get_target1_dist_res() << ","
        << get_target2_x() << "," << get_target2_y() << "," << get_target2_speed() << "," << get_target2_dist_res() << ","
        << get_target3_x() << "," << get_target3_y() << "," << get_target3_speed() << "," << get_target3_dist_res()
        << ") | ";

        // (4) LD2420 (flat doppler × gate array as string)
        ss << ld2420_rdmap_str << "\n";

        // Send the CSI data to the station
        sendto(sock, ss.str().c_str(), strlen(ss.str().c_str()), 0, (struct sockaddr *)&client_addr, sizeof(client_addr));
        total_packet_count++;
        xSemaphoreGive(mutex);
    }
}

void configure_led() {
    gpio_reset_pin(LED_GPIO_PIN);
    gpio_set_direction(LED_GPIO_PIN, GPIO_MODE_OUTPUT);
}

void csi_init() {
    ESP_ERROR_CHECK(esp_wifi_set_csi(1));
    configure_led();

    wifi_csi_config_t configuration_csi;
    configuration_csi.lltf_en = 1;
    configuration_csi.htltf_en = 1;
    configuration_csi.stbc_htltf2_en = 1;
    configuration_csi.ltf_merge_en = 1;
    configuration_csi.channel_filter_en = 0;
    configuration_csi.manu_scale = 0;

    led_timer = xTimerCreate("LedTimer", pdMS_TO_TICKS(1000), pdTRUE, (void *)0, led_timer_callback);
    if (led_timer != NULL) {
        xTimerStart(led_timer, 0);
    }

    ESP_ERROR_CHECK(esp_wifi_set_csi_config(&configuration_csi));
    ESP_ERROR_CHECK(esp_wifi_set_csi_rx_cb(&_wifi_csi_callback, NULL));

    client_addr.sin_family = AF_INET;
    client_addr.sin_port = htons(5000);
    client_addr.sin_addr.s_addr = inet_addr(target_ip);

    sock = socket(AF_INET, SOCK_DGRAM, 0);
}
#endif
