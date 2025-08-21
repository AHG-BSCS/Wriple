#ifndef ESP32_CSI_COMPONENT_H
#define ESP32_CSI_COMPONENT_H

#include <sstream>
#include "driver/gpio.h"
#include "lwip/sockets.h"

#include "mmwave_component.h"

#define LED_GPIO_PIN GPIO_NUM_2
#define LED_PACKET_COUNT_BLINK 15 // Blink every 500 ms
#define CSI_PAYLOAD_SIZE (1344 + LD2420_PAYLOAD_SIZE)

#define CSI_TAG "CSI"

SemaphoreHandle_t mutex = xSemaphoreCreateMutex();
TimerHandle_t led_timer;

static int total_packet_count = 0;
static int sock = -1;
static sockaddr_in client_addr;
static const char *target_ip = "10.59.14.222"; // IP address of the station

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
        wifi_csi_info_t d = data[0];
        std::string payload;
        payload.reserve(CSI_PAYLOAD_SIZE);
    
        char tmp[64];
        // Metadata
        int n = snprintf(tmp, sizeof(tmp), "%llu,%d,%d,%d,%d|",
                         (unsigned long long)d.rx_ctrl.timestamp,
                         d.rx_ctrl.rssi,
                         d.rx_ctrl.cwb,
                         d.rx_ctrl.channel,
                         d.rx_ctrl.ant);
        payload.append(tmp, n);
    
        // CSI bytes as decimal text separated by space
        for (int i = 0; i < d.len; ++i) {
            int m = snprintf(tmp, sizeof(tmp), "%d", (int)d.buf[i]);
            payload.append(tmp, m);
            if (i < d.len - 1) payload.push_back(' ');
        }
        payload.push_back('|');
    
        payload.append(get_ld2420_data());
        payload.push_back('\n');
    
        // Send payload protected by mutex
        xSemaphoreTake(mutex, portMAX_DELAY);
        if (sock != -1) sendto(sock, payload.data(), payload.size(), 0, (struct sockaddr *)&client_addr, sizeof(client_addr));
        
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
