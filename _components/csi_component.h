#ifndef ESP32_CSI_CSI_COMPONENT_H
#define ESP32_CSI_CSI_COMPONENT_H

#include <sstream>
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/timers.h"
#include "lwip/sockets.h"
#include "time_component.h"

#define CSI_RAW 1
#define CSI_AMPLITUDE 0
#define CSI_PHASE 0
#define CSI_TYPE CSI_RAW

SemaphoreHandle_t mutex = xSemaphoreCreateMutex();
TimerHandle_t packet_timer;

static char *project_type;
static const char *CSI = "CSI";

static bool sending = false;
static int packet_count = 0;
static int total_packet_count = 0;

static int sock = -1;
static sockaddr_in client_addr;
static const uint8_t target_mac[6] = {0xE0, 0x2B, 0xE9, 0x95, 0xED, 0x68};
static const char *target_ip = "192.168.4.2";

void packet_timer_callback(TimerHandle_t xTimer) {
    if (sending) {
        ESP_LOGI(CSI, "Total packets sent: %d:", total_packet_count);
        ESP_LOGI(CSI, "Packets sent in 1s: %d\n", packet_count);
        packet_count = 0;  // Reset the packet count for the next interval
    }
}

void _wifi_csi_callback(void *ctx, wifi_csi_info_t *data) {
    if (memcmp(data->mac, target_mac, 6) == 0) {
        sending = true;
        if (sock == -1) {
            ESP_LOGE(CSI, "Unable to create socket");
            vTaskDelete(NULL);
        }

        xSemaphoreTake(mutex, portMAX_DELAY);
        std::stringstream ss;

        wifi_csi_info_t d = data[0];
        char mac[20] = {0};
        sprintf(mac, "%02X:%02X:%02X:%02X:%02X:%02X", d.mac[0], d.mac[1], d.mac[2], d.mac[3], d.mac[4], d.mac[5]);

        ss << "CSI_DATA,"
        << project_type << ","
        << mac << ","
        << d.rx_ctrl.rssi << ","
        << d.rx_ctrl.rate << ","
        << d.rx_ctrl.sig_mode << ","
        << d.rx_ctrl.mcs << ","
        << d.rx_ctrl.cwb << ","
        << d.rx_ctrl.smoothing << ","
        << d.rx_ctrl.not_sounding << ","
        << d.rx_ctrl.aggregation << ","
        << d.rx_ctrl.stbc << ","
        << d.rx_ctrl.fec_coding << ","
        << d.rx_ctrl.sgi << ","
        << d.rx_ctrl.noise_floor << ","
        << d.rx_ctrl.ampdu_cnt << ","
        << d.rx_ctrl.channel << ","
        << d.rx_ctrl.secondary_channel << ","
        << d.rx_ctrl.timestamp << ","
        << d.rx_ctrl.ant << ","
        << d.rx_ctrl.sig_len << ","
        << d.rx_ctrl.rx_state << ","
        << real_time_set << ","
        << get_steady_clock_timestamp() << ","
        << data->len << ",[";

    int data_len = 128;

int8_t *my_ptr;
#if CSI_RAW
    my_ptr = data->buf;
    for (int i = 0; i < data_len; i++) {
        ss << (int) my_ptr[i] << " ";
    }
#endif
#if CSI_AMPLITUDE
    my_ptr = data->buf;
    for (int i = 0; i < data_len / 2; i++) {
        ss << (int) sqrt(pow(my_ptr[i * 2], 2) + pow(my_ptr[(i * 2) + 1], 2)) << " ";
    }
#endif
#if CSI_PHASE
    my_ptr = data->buf;
    for (int i = 0; i < data_len / 2; i++) {
        ss << (int) atan2(my_ptr[i*2], my_ptr[(i*2)+1]) << " ";
    }
#endif
        ss << "]\n";
        // Send the CSI data to the target IP
        sendto(sock, ss.str().c_str(), strlen(ss.str().c_str()), 0, (struct sockaddr *)&client_addr, sizeof(client_addr));
        
        packet_count++;
        total_packet_count++;

        fflush(stdout);
        vTaskDelay(0);
        xSemaphoreGive(mutex);
    }
    else {
        sending = false;
    }
}

void csi_init(char *type) {
    project_type = type;
    ESP_ERROR_CHECK(esp_wifi_set_csi(1));

    wifi_csi_config_t configuration_csi;
    configuration_csi.lltf_en = 1;
    configuration_csi.htltf_en = 1;
    configuration_csi.stbc_htltf2_en = 1;
    configuration_csi.ltf_merge_en = 1;
    configuration_csi.channel_filter_en = 0;
    configuration_csi.manu_scale = 0;

    packet_timer = xTimerCreate("PacketTimer", pdMS_TO_TICKS(1000), pdTRUE, (void *)0, packet_timer_callback);
    if (packet_timer != NULL) {
        xTimerStart(packet_timer, 0);
    }

    ESP_ERROR_CHECK(esp_wifi_set_csi_config(&configuration_csi));
    ESP_ERROR_CHECK(esp_wifi_set_csi_rx_cb(&_wifi_csi_callback, NULL));

    client_addr.sin_family = AF_INET;
    client_addr.sin_port = htons(5000);
    client_addr.sin_addr.s_addr = inet_addr(target_ip);

    sock = socket(AF_INET, SOCK_DGRAM, 0);
}
#endif
