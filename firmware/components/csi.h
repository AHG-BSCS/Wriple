#ifndef CSI_COMPONENT_H
#define CSI_COMPONENT_H

#include <sstream>
#include "driver/gpio.h"

#include "rdm.h"
#include "server.h"

#define CSI_TAG "CSI"

#define LED_PIN GPIO_NUM_2
#define LED_BLINK_INTERVAL  15 // Blink every 500 ms if 30 packets/sec
#define CSI_PAYLOAD_SIZE    (1344 + RDM_PAYLOAD_SIZE)

extern int server_sock;
extern struct sockaddr_in server_addr;
extern socklen_t server_addr_len;

static SemaphoreHandle_t mutex = xSemaphoreCreateMutex();
static bool is_led_high = false;
static int total_packet_count = 0;

void blink_led() {
    if (total_packet_count == 0) {
        is_led_high = !is_led_high;
        gpio_set_level(LED_PIN, is_led_high);
        total_packet_count = LED_BLINK_INTERVAL;
    }
}

void _wifi_csi_callback(void *ctx, wifi_csi_info_t *data) {
    // Common signal length: 14, 114
    // ESP_LOGI(CSI_TAG, "%d bytes", data[0].rx_ctrl.sig_len);
    // ESP_LOGI(CSI_TAG, "%d channel", data[0].rx_ctrl.cwb);

    // If from 20Mhz Channel with specific payload length
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
    
        payload.append(get_rdm_data());
        payload.push_back('\n');
    
        // Send payload protected by mutex
        xSemaphoreTake(mutex, portMAX_DELAY);
        if (server_sock != -1) sendto(server_sock, payload.data(), payload.size(), 0,
                                      (struct sockaddr *)&server_addr, server_addr_len);
        
        blink_led();
        total_packet_count--;
        xSemaphoreGive(mutex);
    }
    // Start signal capturing
    else if (data[0].rx_ctrl.sig_len == 87) {
        is_led_high = true;
        total_packet_count = 0;
        gpio_set_level(LED_PIN, is_led_high);
        discover_server_address();
    }
    // Stop signal capturing
    else if (data[0].rx_ctrl.sig_len == 86) {
        is_led_high = false;
        total_packet_count = 0;
        gpio_set_level(LED_PIN, is_led_high);
        ESP_LOGI(CSI_TAG, "Stop signal received");
    }
}

void csi_init() {
    gpio_reset_pin(LED_PIN);
    ESP_ERROR_CHECK(gpio_set_direction(LED_PIN, GPIO_MODE_OUTPUT));

    wifi_csi_config_t csi_config;
    csi_config.lltf_en = 1;
    csi_config.htltf_en = 1;
    csi_config.stbc_htltf2_en = 1;
    csi_config.ltf_merge_en = 1;
    csi_config.channel_filter_en = 0;
    csi_config.manu_scale = 0;

    ESP_ERROR_CHECK(esp_wifi_set_csi_config(&csi_config));
    ESP_ERROR_CHECK(esp_wifi_set_csi_rx_cb(&_wifi_csi_callback, NULL));
    ESP_ERROR_CHECK(esp_wifi_set_csi(1));
}

#endif
