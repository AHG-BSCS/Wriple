#ifndef RD03D_RADAR_COMPONENT_H
#define RD03D_RADAR_COMPONENT_H

#define RD03D_UART_PORT      UART_NUM_1
#define RD03D_UART_WAIT      5 / portTICK_PERIOD_MS // 5 ms (Keep it low for low latency read)
#define RD03D_BAUD_RATE      256000
#define RD03D_UART_BUF_SIZE  256
#define RD03D_TX_PIN         17
#define RD03D_RX_PIN         16

// Multi-target detection mode header and tail bytes
#define RD03D_HEADER_1  0xAA
#define RD03D_HEADER_2  0xFF
#define RD03D_HEADER_3  0x03
#define RD03D_HEADER_4  0x00
#define RD03D_TAIL_1    0x55
#define RD03D_TAIL_2    0xCC

#define RD03D_HEADER_LEN  4
#define RD03D_TAIL_LEN    2
#define RD03D_FRAME_SIZE  30 // 4 bytes header + 8 * 3 bytes target data + 2 bytes tail
#define RD03D_BUF_SIZE    128

#define RD03D_TIMER_INTERVAL 333 // RD03D updates every 100 ms in multi-target mode
#define RD03D_READ_INTERVAL  100000
#define RD03D_TAG "RD03D"

static int64_t last_rd03d_read_time = 0;
static TimerHandle_t rd03d_timer;
static TaskHandle_t rd03d_task_handle = NULL;
static uint8_t rd03d_buffer[RD03D_BUF_SIZE];

void parse_single_target(const uint8_t* buf, bool& is_updated, int16_t& x, int16_t& y, int16_t& speed, 
                         uint16_t& dist_res, const int target_num) {
    if (buf[0] != 0x00 && buf[1] != 0x00) {
        is_updated = true;
        uint16_t x_raw = buf[0] | (buf[1] << 8);
        x = (x_raw & 0x7FFF) * ((x_raw & 0x8000) ? -1 : 1);
        uint16_t y_raw = buf[2] | (buf[3] << 8);
        y = (y_raw & 0x7FFF) * ((y_raw & 0x8000) ? 1 : -1);
        uint16_t speed_raw = buf[4] | (buf[5] << 8);
        speed = (speed_raw & 0x7FFF) * ((speed_raw & 0x8000) ? -1 : 1);
        dist_res = buf[6] | (buf[7] << 8);
        // ESP_LOGI(RD03D_TAG, "Target %d - X: %d mm, Y: %d mm, Speed: %d cm/s, Dist_Res: %d mm", 
        //     target_num, x, y, speed, dist_res);
    } else {
        is_updated = false;
    }
}

std::string get_rd03d_data() {
    int64_t current_time = esp_timer_get_time();
    // Read data only if at least 100 ms have passed since the last read
    if (current_time - last_rd03d_read_time < RD03D_READ_INTERVAL) return "!";
    last_rd03d_read_time = current_time;

    int len = uart_read_bytes(RD03D_UART_PORT, rd03d_buffer, RD03D_BUF_SIZE, RD03D_UART_WAIT);

    if (len < RD03D_FRAME_SIZE) {
        ESP_LOGW(RD03D_TAG, "Not enough data (%d bytes)", len);
        return "!";
    }

    for (int i = 0; i <= RD03D_BUF_SIZE / 2; i++) {
        // Check for valid frame header and tail
        int tail_idx = i + RD03D_FRAME_SIZE - RD03D_TAIL_LEN;
        if (rd03d_buffer[i] == RD03D_HEADER_1 &&
            rd03d_buffer[i + 1] == RD03D_HEADER_2 &&
            rd03d_buffer[i + 2] == RD03D_HEADER_3 &&
            rd03d_buffer[i + 3] == RD03D_HEADER_4 &&
            rd03d_buffer[tail_idx] == RD03D_TAIL_1 &&
            rd03d_buffer[tail_idx + 1] == RD03D_TAIL_2)
        {
            // Parse raw data
            int16_t x[3] = {0}, y[3] = {0}, speed[3] = {0};
            uint16_t dist_res[3] = {0};
            bool updated[3] = {false};

            for (int i = 0; i < 3; ++i) {
                parse_single_target(&rd03d_buffer[4 + i * 8], updated[i], x[i], y[i], speed[i], dist_res[i], i + 1);
            }

            std::stringstream ss;
            for (int i = 0; i < 3; ++i) {
                ss << x[i] << "," << y[i] << "," << speed[i] << "," << dist_res[i];
                if (i < 2) ss << ",";
            }

            // ESP_LOGI(RD03D_TAG, "Valid data frame parsed at index %d", i);
            return ss.str();
        }
    }
    
    ESP_LOGW(RD03D_TAG, "No valid data frame found in %d bytes", len);
    return "!";
}


void rd03d_timer_callback(TimerHandle_t xTimer) {
    if (rd03d_task_handle) xTaskNotifyGive(rd03d_task_handle);
}

void rd03d_task(void *pvParameters) {
    while (1) {
        ulTaskNotifyTake(pdTRUE, portMAX_DELAY);
        get_rd03d_data();
    }
}

void start_rd03d_timer() {
    if (rd03d_task_handle == NULL)
        xTaskCreate(rd03d_task, "RD03D_Task", 4096, NULL, 10, &rd03d_task_handle);

    rd03d_timer = xTimerCreate("RD03D_Timer", pdMS_TO_TICKS(RD03D_TIMER_INTERVAL), pdTRUE, (void *)0, rd03d_timer_callback);
    xTimerStart(rd03d_timer, 0);
}

void rd03d_init() {
    uart_config_t uart_config = {
        .baud_rate = RD03D_BAUD_RATE,
        .data_bits = UART_DATA_8_BITS,
        .parity    = UART_PARITY_DISABLE,
        .stop_bits = UART_STOP_BITS_1,
        .flow_ctrl = UART_HW_FLOWCTRL_DISABLE,
        .rx_flow_ctrl_thresh = 122,   // Default threshold value
        .source_clk = UART_SCLK_DEFAULT,
        .flags = 0
    };

    uart_param_config(RD03D_UART_PORT, &uart_config);
    uart_set_pin(RD03D_UART_PORT, RD03D_TX_PIN, RD03D_RX_PIN, UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE);
    uart_driver_install(RD03D_UART_PORT, RD03D_UART_BUF_SIZE, 0, 0, NULL, 0);
    
    // Send multi-target detection mode command
    // uint8_t single_target_cmd[12] = {0xFD, 0xFC, 0xFB, 0xFA, 0x02, 0x00, 0x80, 0x00, 0x04, 0x03, 0x02, 0x01};
    uint8_t multi_target_cmd[12] = {0xFD, 0xFC, 0xFB, 0xFA, 0x02, 0x00, 0x90, 0x00, 0x04, 0x03, 0x02, 0x01};
    uart_write_bytes(RD03D_UART_PORT, (const char *)multi_target_cmd, sizeof(multi_target_cmd));
    ESP_LOGI(RD03D_TAG, "RD03D Mode: Multi-target.");

    // Temporary timer for debugging
    // start_rd03d_timer();
}

#endif
