#ifndef LD2420_RADAR_COMPONENT_H
#define LD2420_RADAR_COMPONENT_H

#define LD2420_UART_PORT    UART_NUM_2
#define LD2420_UART_TICK    110 // Lower than 100 ms cause the buffer to be insufficient
#define LD2420_BAUD_RATE    115200
#define UART_BUF_SIZE       256
#define LD2420_TX_PIN       19
#define LD2420_RX_PIN       18
#define TIMER_PERIOD        250 // Greater than 450 ms cause a timing issue with data buffer

#define DEBUG_HEADER_1    0xAA
#define DEBUG_HEADER_2    0xBF
#define DEBUG_HEADER_3    0x10
#define DEBUG_HEADER_4    0x14
#define DEBUG_TAIL_1      0xFD
#define DEBUG_TAIL_2      0xFC
#define DEBUG_TAIL_3      0xFB
#define DEBUG_TAIL_4      0xFA

#define DEBUG_HEADER_LEN    4
#define DEBUG_TAIL_LEN      4
#define DEBUG_FRAME_SIZE    1288 // 4 bytes header + 1280 bytes RDMAP data + 4 bytes tail
#define DEBUG_BUF_SIZE      2700 // Double the size with  of debug frame size to ensure a full frames

#define DOPPLER_BINS  20
#define GATES         16

#define LD2420_TAG "LD2420"

static TimerHandle_t ld2420_timer;
static TaskHandle_t ld2420_task_handle = NULL;

static uint8_t ld2420_buffer[DEBUG_BUF_SIZE];
uint32_t ld2420_rdmap[DOPPLER_BINS][GATES];

bool     ld2420_presence       = false;
uint16_t ld2420_distance_mm    = 0;
uint16_t ld2420_energy[16]     = {0};

void parse_ld2420_debug_data() {
    int len = uart_read_bytes(LD2420_UART_PORT, ld2420_buffer, DEBUG_BUF_SIZE, LD2420_UART_TICK / portTICK_PERIOD_MS);

    if (len < DEBUG_FRAME_SIZE) {
        ESP_LOGW(LD2420_TAG, "Not enough data (%d bytes)", len);
        return;
    }
    ESP_LOGW(LD2420_TAG, "Buffer Lenght: (%d bytes)", len);

    // Look for index of the header in half of the buffer
    for (int i = 0; i <= len - DEBUG_BUF_SIZE / 2; i++) {
        if (ld2420_buffer[i] == DEBUG_HEADER_1 &&
            ld2420_buffer[i+1] == DEBUG_HEADER_2 &&
            ld2420_buffer[i+2] == DEBUG_HEADER_3 &&
            ld2420_buffer[i+3] == DEBUG_HEADER_4) 
        {
            int tail_idx = i + DEBUG_FRAME_SIZE - DEBUG_TAIL_LEN;
            if (ld2420_buffer[tail_idx] != DEBUG_TAIL_1 ||
                ld2420_buffer[tail_idx+1] != DEBUG_TAIL_2 ||
                ld2420_buffer[tail_idx+2] != DEBUG_TAIL_3 ||
                ld2420_buffer[tail_idx+3] != DEBUG_TAIL_4) 
            {
                ESP_LOGW(LD2420_TAG, "Invalid debug frame tail");
                continue;
            }

            const uint8_t* rdmap_data = &ld2420_buffer[i + DEBUG_HEADER_LEN];

            // Parse 20 Doppler bins × 16 gates × 4 bytes = 1280 bytes
            for (int doppler = 0; doppler < DOPPLER_BINS; doppler++) {
                for (int gate = 0; gate < GATES; gate++) {
                    int idx = (doppler * GATES + gate) * 4;
                    uint32_t val = 0;
                    val |= rdmap_data[idx];
                    val |= ((uint32_t)rdmap_data[idx+1]) << 8;
                    val |= ((uint32_t)rdmap_data[idx+2]) << 16;
                    val |= ((uint32_t)rdmap_data[idx+3]) << 24;
                    ld2420_rdmap[doppler][gate] = val;
                }
            }

            ESP_LOGI(LD2420_TAG, "RDMAP data parsed:");
            // for (int doppler = 0; doppler < DOPPLER_BINS; doppler++) {
            //     printf("Doppler %2d: ", doppler);
            //     for (int gate = 0; gate < GATES; gate++) {
            //         printf("%6u ", (unsigned int)ld2420_rdmap[doppler][gate]);
            //     }
            //     printf("\n");
            // }
            return;
        }
    }

    ESP_LOGW(LD2420_TAG, "No valid debug frame found");
}

void ld2420_timer_callback(TimerHandle_t xTimer) {
    if (ld2420_task_handle) xTaskNotifyGive(ld2420_task_handle);
}

void ld2420_task(void *pvParameters) {
    while (1) {
        ulTaskNotifyTake(pdTRUE, portMAX_DELAY);
        parse_ld2420_debug_data();
    }
}

void start_ld2420_timer() {
    if (ld2420_task_handle == NULL)
        xTaskCreate(ld2420_task, "LD2420Task", 4096, NULL, 10, &ld2420_task_handle);

    ld2420_timer = xTimerCreate("LD2420Timer", pdMS_TO_TICKS(TIMER_PERIOD), pdTRUE, (void *)0, ld2420_timer_callback);
    xTimerStart(ld2420_timer, 0);
}

void ld2420_init() {
    uart_config_t uart_config = {
        .baud_rate = LD2420_BAUD_RATE,
        .data_bits = UART_DATA_8_BITS,
        .parity    = UART_PARITY_DISABLE,
        .stop_bits = UART_STOP_BITS_1,
        .flow_ctrl = UART_HW_FLOWCTRL_DISABLE,
        .rx_flow_ctrl_thresh = 122,   // Default threshold value
        .source_clk = UART_SCLK_DEFAULT,
        .flags = 0
    };

    uart_param_config(LD2420_UART_PORT, &uart_config);
    uart_set_pin(LD2420_UART_PORT, LD2420_TX_PIN, LD2420_RX_PIN, UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE);
    uart_driver_install(LD2420_UART_PORT, UART_BUF_SIZE, 0, 0, NULL, 0);

    // Send debug mode command to receive debug data
    uint8_t debug_cmd[18] = {0xFD, 0xFC, 0xFB, 0xFA, 0x08, 0x00, 0x12, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x04, 0x03, 0x02, 0x01};
    uart_write_bytes(LD2420_UART_PORT, (const char *)debug_cmd, sizeof(debug_cmd));
    ESP_LOGI(LD2420_TAG, "Debug mode activated.");
    // Temporary timer for debugging
    start_ld2420_timer();
}

#endif
