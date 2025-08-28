#ifndef RDM_COMPONENT_H
#define RDM_COMPONENT_H

#include <inttypes.h>
#include "driver/uart.h"
#include "esp_timer.h"

#define RDM_TAG "RDM"

#define LD2420_UART_PORT    UART_NUM_1
#define LD2420_UART_WAIT    5 / portTICK_PERIOD_MS // 5 ms (Keep it low for low latency read)
#define LD2420_BAUD_RATE    115200
#define LD2420_TX_PIN       19
#define LD2420_RX_PIN       18

// Debug mode header and tail bytes
#define LD2420_HEADER_1    0xAA
#define LD2420_HEADER_2    0xBF
#define LD2420_HEADER_3    0x10
#define LD2420_HEADER_4    0x14
#define LD2420_TAIL_1      0xFD
#define LD2420_TAIL_2      0xFC
#define LD2420_TAIL_3      0xFB
#define LD2420_TAIL_4      0xFA

#define LD2420_HEADER_LEN    4
#define LD2420_TAIL_LEN      4
#define LD2420_FRAME_SIZE    1288 // 4 bytes header + 1280 bytes RDMAP data + 4 bytes tail
#define LD2420_BUF_SIZE      2700 // Double the size with of debug frame size to ensure a full frames

#define DOPPLER_BINS    20
#define RANGE_GATES     16
#define RDM_PAYLOAD_SIZE  (DOPPLER_BINS * RANGE_GATES * 3)

// #define LD2420_TIMER_INTERVAL  333 // LD2420 updates every 300 ms in debug mode
#define LD2420_READ_INTERVAL   333000

static int64_t last_ld2420_read_time = 0;
// static TimerHandle_t ld2420_timer;
// static TaskHandle_t ld2420_task_handle = NULL;
static uint8_t ld2420_buffer[LD2420_BUF_SIZE];

// static bool ld242_presence = false;
// static uint16_t ld242_distance_mm = 0;
// static uint16_t ld242_energy[16] = {0};

std::string get_rdm_data() {
    int64_t current_time = esp_timer_get_time();
    // Read data only if at least 333 ms have passed since the last read
    if (current_time - last_ld2420_read_time < LD2420_READ_INTERVAL) return "!";
    last_ld2420_read_time = current_time;

    int len = uart_read_bytes(LD2420_UART_PORT, ld2420_buffer, LD2420_BUF_SIZE, LD2420_UART_WAIT);

    if (len < LD2420_FRAME_SIZE) {
        ESP_LOGW(RDM_TAG, "Insufficient data: %d bytes", len);
        return "!";
    }

    // Look for index of the header in half of the buffer
    for (int i = 0; i <= LD2420_BUF_SIZE / 2; i++) {
        // Check for valid frame header and tail
        int tail_idx = i + LD2420_FRAME_SIZE - LD2420_TAIL_LEN;
        if (ld2420_buffer[i] == LD2420_HEADER_1 &&
            ld2420_buffer[i + 1] == LD2420_HEADER_2 &&
            ld2420_buffer[i + 2] == LD2420_HEADER_3 &&
            ld2420_buffer[i + 3] == LD2420_HEADER_4 &&
            ld2420_buffer[tail_idx] == LD2420_TAIL_1 &&
            ld2420_buffer[tail_idx + 1] == LD2420_TAIL_2 &&
            ld2420_buffer[tail_idx + 2] == LD2420_TAIL_3 &&
            ld2420_buffer[tail_idx + 3] == LD2420_TAIL_4)
        {
            const uint8_t* rdmap_data = &ld2420_buffer[i + LD2420_HEADER_LEN];

            // Reserve enough space
            std::string out;
            out.reserve(RDM_PAYLOAD_SIZE);

            char tmp[16];
            for (int doppler = 0; doppler < DOPPLER_BINS; doppler++) {
                for (int gate = 0; gate < RANGE_GATES; gate++) {
                    int idx = (doppler * RANGE_GATES + gate) * 4;
                    uint32_t val = 0;
                    val |= rdmap_data[idx];
                    val |= ((uint32_t)rdmap_data[idx + 1]) << 8;
                    val |= ((uint32_t)rdmap_data[idx + 2]) << 16;
                    val |= ((uint32_t)rdmap_data[idx + 3]) << 24;

                    int n = snprintf(tmp, sizeof(tmp), "%" PRIu32, val);
                    out.append(tmp, (n > 0) ? n : 0);

                    if (!(doppler == DOPPLER_BINS - 1 && gate == RANGE_GATES - 1)) {
                        out.push_back(',');
                    }
                }
            }

            return out;
        }
    }

    ESP_LOGW(RDM_TAG, "No valid frame: %d bytes", len);
    return "!";
}

// void read_ld2420_report_mode() {
//     int len = uart_read_bytes(LD2420_UART_PORT, ld2420_buffer, LD2420_BUF_SIZE, LD2420_UART_WAIT);
//     if (len < 8) {
//         ESP_LOGW(RDM_TAG, "Insufficient data: %d bytes", len);
//         return;
//     }

//     for (int i = 0; i <= len - 8; i++) {
//         if (ld2420_buffer[i]   == 0xF4 &&
//             ld2420_buffer[i+1] == 0xF3 &&
//             ld2420_buffer[i+2] == 0xF2 &&
//             ld2420_buffer[i+3] == 0xF1)
//         {
//             // length field: total payload bytes (detection + distance + 32 bytes energy)
//             uint16_t payload_len = ld2420_buffer[i+4] | (ld2420_buffer[i+5] << 8);
//             int frame_size = 4 + 2 + payload_len + 4;

//             // make sure the full frame is in the buffer
//             if (i + frame_size > len) {
//                 ESP_LOGW(RDM_TAG, "Frame incomplete: need %d bytes, have %d bytes", frame_size, len - i);
//                 return;
//             }

//             const uint8_t *p = ld2420_buffer + i + 6;
//             ld242_presence    = (p[0] == 0x01);
//             ld242_distance_mm = p[1] | (p[2] << 8);

//             for (int gate = 0; gate < 16; gate++) {
//                 int idx = 3 + gate*2;
//                 ld242_energy[gate] = p[idx] | (p[idx+1] << 8);
//             }

//             ESP_LOGI(RDM_TAG, "Presence: %s, Distance: %d mm",
//                      ld242_presence ? "YES" : "NO", ld242_distance_mm);
//             for (int g = 0; g < 16; g++) {
//                 ESP_LOGI(RDM_TAG, " Gate %2d: Energy = %5d", g, ld242_energy[g]);
//             }
//             return;
//         }
//         ESP_LOGW(RDM_TAG, "No valid frame: %d bytes", len);
//     }
// }

// void ld2420_timer_callback(TimerHandle_t xTimer) {
//     if (ld2420_task_handle) xTaskNotifyGive(ld2420_task_handle);
// }

// void ld2420_task(void *pvParameters) {
//     while (1) {
//         ulTaskNotifyTake(pdTRUE, portMAX_DELAY);
//         get_rdm_data();
//         // read_ld2420_report_mode();
//     }
// }

// void start_ld2420_timer() {
//     if (ld2420_task_handle == NULL)
//         xTaskCreate(ld2420_task, "LD2420_Task", 4096, NULL, 10, &ld2420_task_handle);

//     ld2420_timer = xTimerCreate("LD2420_Timer", pdMS_TO_TICKS(LD2420_TIMER_INTERVAL),
//                                 pdTRUE, (void *)0, ld2420_timer_callback);
//     xTimerStart(ld2420_timer, 0);
// }

void rdm_init() {
    uart_config_t uart_config = {
        .baud_rate = LD2420_BAUD_RATE,
        .data_bits = UART_DATA_8_BITS,
        .parity    = UART_PARITY_DISABLE,
        .stop_bits = UART_STOP_BITS_1,
        .flow_ctrl = UART_HW_FLOWCTRL_DISABLE,
        .rx_flow_ctrl_thresh = 122, // Default threshold value
        .source_clk = UART_SCLK_DEFAULT,
        .flags = 0
    };

    ESP_ERROR_CHECK(uart_param_config(LD2420_UART_PORT, &uart_config));
    ESP_ERROR_CHECK(uart_set_pin(LD2420_UART_PORT, LD2420_TX_PIN, LD2420_RX_PIN,
                                 UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE));
    ESP_ERROR_CHECK(uart_driver_install(LD2420_UART_PORT, LD2420_BUF_SIZE, 0, 0, NULL, 0));

    // Send debug mode command to receive debug data
    // uint8_t normal_cmd[18] = {0xFD, 0xFC, 0xFB, 0xFA, 0x08, 0x00, 0x12, 0x00, 0x00, 0x00, 0x64, 0x00, 0x00, 0x00, 0x04, 0x03, 0x02, 0x01};
    // uint8_t report_cmd[18] = {0xFD, 0xFC, 0xFB, 0xFA, 0x08, 0x00, 0x12, 0x00, 0x00, 0x00, 0x04, 0x00, 0x00, 0x00, 0x04, 0x03, 0x02, 0x01};
    uint8_t debug_cmd[18] = {0xFD, 0xFC, 0xFB, 0xFA, 0x08, 0x00, 0x12, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x04, 0x03, 0x02, 0x01};
    int written = uart_write_bytes(LD2420_UART_PORT, (const char *)debug_cmd, sizeof(debug_cmd));
    if (written < 0) ESP_LOGW(RDM_TAG, "Radar command failed: %d", written);
    ESP_LOGI(RDM_TAG, "LD2420 Mode: Debug");

    // Temporary timer for debugging
    // start_ld2420_timer();
}

#endif
