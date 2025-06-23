#ifndef RD03D_RADAR_COMPONENT_H
#define RD03D_RADAR_COMPONENT_H

#define RD03D_UART_PORT     UART_NUM_1
#define RD03D_BAUD_RATE     256000
#define RD03D_UART_BUF_SIZE 256
#define RD03D_BUF_SIZE      32
#define RD03D_TX_PIN        17
#define RD03D_RX_PIN        16
#define RD03D_TIMER_PERIOD  50 // Less than 45 ms is too fast for rd-03d to send data

// Multi-target detection mode header and tail bytes
#define RD03D_HEADER_1  0xAA
#define RD03D_HEADER_2  0xFF
#define RD03D_HEADER_3  0x03
#define RD03D_HEADER_4  0x00
#define RD03D_TAIL_1    0x55
#define RD03D_TAIL_2    0xCC

#define RD03D_FRAME_SIZE 30 // 4 bytes header + 8 * 3 bytes target data + 2 bytes tail

#define RD03D_TAG "RD03D"

static TimerHandle_t rd03d_timer;
static TaskHandle_t rd03d_task_handle = NULL;
static uint8_t rd03d_buffer[RD03D_BUF_SIZE];

bool target1_updated = false;
int16_t target1_x = 0;
int16_t target1_y = 0;
int16_t target1_speed = 0;
uint16_t target1_dist_res = 0;

bool target2_updated = false;
int16_t target2_x = 0;
int16_t target2_y = 0;
int16_t target2_speed = 0;
uint16_t target2_dist_res = 0;

bool target3_updated = false;
int16_t target3_x = 0;
int16_t target3_y = 0;
int16_t target3_speed = 0;
uint16_t target3_dist_res = 0;

int16_t get_target1_x() {
    if (target1_updated) return target1_x;
    else return 0;
}

int16_t get_target1_y() {
    if (target1_updated) return target1_y;
    else return 0;
}

int16_t get_target1_speed() {
    if (target1_updated) return target1_speed;
    else return 0;
}

uint16_t get_target1_dist_res() {
    if (target1_updated) return target1_dist_res;
    else return 0;
}

int16_t get_target2_x() {
    if (target2_updated) return target2_x;
    else return 0;
}

int16_t get_target2_y() {
    if (target2_updated) return target2_y;
    else return 0;
}

int16_t get_target2_speed() {
    if (target2_updated) return target2_speed;
    else return 0;
}

uint16_t get_target2_dist_res() {
    if (target2_updated) return target2_dist_res;
    else return 0;
}

int16_t get_target3_x() {
    if (target3_updated) return target3_x;
    else return 0;
}

int16_t get_target3_y() {
    if (target3_updated) return target3_y;
    else return 0;
}

int16_t get_target3_speed() {
    if (target3_updated) return target3_speed;
    else return 0;
}

uint16_t get_target3_dist_res() {
    if (target3_updated) return target3_dist_res;
    else return 0;
}

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

void parse_targets(const uint8_t* buf) {
    parse_single_target(&buf[0], target1_updated, target1_x, target1_y, 
                        target1_speed, target1_dist_res, 1);
    parse_single_target(&buf[8], target2_updated, target2_x, target2_y, 
                        target2_speed, target2_dist_res, 2);
    parse_single_target(&buf[16], target3_updated, target3_x, target3_y, 
                        target3_speed, target3_dist_res, 3);
}

void read_radar_data() {
    int len = uart_read_bytes(RD03D_UART_PORT, rd03d_buffer, RD03D_BUF_SIZE, RD03D_TIMER_PERIOD / portTICK_PERIOD_MS);
    
    if (len < RD03D_FRAME_SIZE) {
        ESP_LOGW(RD03D_TAG, "Not enough data (%d bytes)", len);
        return;
    }

    // Check for valid frame header and tail
    if (rd03d_buffer[0] == RD03D_HEADER_1 &&
        rd03d_buffer[1] == RD03D_HEADER_2 &&
        rd03d_buffer[2] == RD03D_HEADER_3 &&
        rd03d_buffer[3] == RD03D_HEADER_4 &&
        rd03d_buffer[28] == RD03D_TAIL_1 &&
        rd03d_buffer[29] == RD03D_TAIL_2)
    {
        parse_targets(&rd03d_buffer[4]);
        ESP_LOGI(RD03D_TAG, "Valid data frame parsed");
        return;
    }

    ESP_LOGW(RD03D_TAG, "No valid RD03D data frame found");
}

void rd03d_timer_callback(TimerHandle_t xTimer) {
    if (rd03d_task_handle) xTaskNotifyGive(rd03d_task_handle);
}

void rd03d_task(void *pvParameters) {
    while (1) {
        ulTaskNotifyTake(pdTRUE, portMAX_DELAY);
        read_radar_data();
    }
}

void start_rd03d_timer() {
    if (rd03d_task_handle == NULL)
        xTaskCreate(rd03d_task, "RD03D_Task", 4096, NULL, 10, &rd03d_task_handle);

    rd03d_timer = xTimerCreate("RD03D_Timer", pdMS_TO_TICKS(RD03D_TIMER_PERIOD), pdTRUE, (void *)0, rd03d_timer_callback);
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
    uint8_t multi_target_cmd[12] = {0xFD, 0xFC, 0xFB, 0xFA, 0x02, 0x00, 0x90, 0x00, 0x04, 0x03, 0x02, 0x01};
    uart_write_bytes(RD03D_UART_PORT, (const char *)multi_target_cmd, sizeof(multi_target_cmd));
    ESP_LOGI(RD03D_TAG, "RD03D Mode: Multi-target.");

    // Temporary timer for debugging
    // start_rd03d_timer();
}

#endif
