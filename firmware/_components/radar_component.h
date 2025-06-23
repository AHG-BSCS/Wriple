#ifndef RD03D_RADAR_COMPONENT_H
#define RD03D_RADAR_COMPONENT_H

#define RD03D_HEADER_BYTE_1 0xAA
#define RD03D_HEADER_BYTE_2 0xFF
#define RD03D_HEADER_BYTE_3 0x03
#define RD03D_HEADER_BYTE_4 0x00
// #define RD03D_TAIL_BYTE_1 0x55
// #define RD03D_TAIL_BYTE_2 0xCC

#include "driver/uart.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "string.h"
#include "math.h"
#include "esp_log.h"

#define RD03D_UART_PORT UART_NUM_1
#define RD03D_BUF_SIZE  512
#define RD03D_TX_PIN    17
#define RD03D_RX_PIN    16
#define RD03D_BAUD_RATE 256000

static const char *RD03D_TAG = "RD03D";
static uint8_t radar_data_buffer[RD03D_BUF_SIZE];

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
    uart_driver_install(RD03D_UART_PORT, RD03D_BUF_SIZE, 0, 0, NULL, 0);
    
    // Send multi-target detection mode command
    uint8_t cmd[12] = {0xFD, 0xFC, 0xFB, 0xFA, 0x02, 0x00, 0x90, 0x00, 0x04, 0x03, 0x02, 0x01};
    uart_write_bytes(RD03D_UART_PORT, (const char *)cmd, sizeof(cmd));
    ESP_LOGI(RD03D_TAG, "RD03D Mode: Multi-target.");
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
        ESP_LOGI(RD03D_TAG, "Target %d - X: %d mm, Y: %d mm, Speed: %d cm/s, Dist_Res: %d mm", 
            target_num, x, y, speed, dist_res);
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
    int len = uart_read_bytes(RD03D_UART_PORT, radar_data_buffer, RD03D_BUF_SIZE, 20 / portTICK_PERIOD_MS);
    if (len > 0) {
        for (int i = 0; i < len - 6; i++) {
            if (radar_data_buffer[i] == RD03D_HEADER_BYTE_1 && radar_data_buffer[i+1] == RD03D_HEADER_BYTE_2 &&
                radar_data_buffer[i+2] == RD03D_HEADER_BYTE_3 && radar_data_buffer[i+3] == RD03D_HEADER_BYTE_4) {
                parse_targets(&radar_data_buffer[i + 4]);
                break; // Get the first one only
            }
        }
    }
}
#endif
