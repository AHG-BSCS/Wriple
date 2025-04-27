#ifndef RD03D_RADAR_COMPONENT_H
#define RD03D_RADAR_COMPONENT_H

#include "driver/uart.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "string.h"
#include "math.h"
#include "esp_log.h"

#define RD03D_UART_PORT UART_NUM_1
#define RD03D_BUF_SIZE  256
#define RD03D_TX_PIN    17
#define RD03D_RX_PIN    16
#define RD03D_BAUD_RATE 256000

static const char *RADAR_TAG = "RD03D";

bool is_single_target = true;
uint8_t radar_rx_buf[64] = {0};

bool is_target1_updated = false;
int16_t target1_x = 0;
int16_t target1_y = 0;
int16_t target1_speed = 0;
uint16_t target1_dist_res = 0;

bool is_target2_updated = false;
int16_t target2_x = 0;
int16_t target2_y = 0;
int16_t target2_speed = 0;
uint16_t target2_dist_res = 0;

bool is_target3_updated = false;
int16_t target3_x = 0;
int16_t target3_y = 0;
int16_t target3_speed = 0;
uint16_t target3_dist_res = 0;

int16_t get_target1_x() {
    if (is_target1_updated) return target1_x;
    else return 0;
}

int16_t get_target1_y() {
    if (is_target1_updated) return target1_y;
    else return 0;
}

int16_t get_target1_speed() {
    if (is_target1_updated) return target1_speed;
    else return 0;
}

uint16_t get_target1_dist_res() {
    if (is_target1_updated) return target1_dist_res;
    else return 0;
}

int16_t get_target2_x() {
    if (is_target2_updated) return target2_x;
    else return 0;
}

int16_t get_target2_y() {
    if (is_target2_updated) return target2_y;
    else return 0;
}

int16_t get_target2_speed() {
    if (is_target2_updated) return target2_speed;
    else return 0;
}

uint16_t get_target2_dist_res() {
    if (is_target2_updated) return target2_dist_res;
    else return 0;
}

int16_t get_target3_x() {
    if (is_target3_updated) return target3_x;
    else return 0;
}

int16_t get_target3_y() {
    if (is_target3_updated) return target3_y;
    else return 0;
}

int16_t get_target3_speed() {
    if (is_target3_updated) return target3_speed;
    else return 0;
}

uint16_t get_target3_dist_res() {
    if (is_target3_updated) return target3_dist_res;
    else return 0;
}

void rd03d_init() {
    uart_config_t uart_config = {
        .baud_rate = RD03D_BAUD_RATE,
        .data_bits = UART_DATA_8_BITS,
        .parity    = UART_PARITY_DISABLE,
        .stop_bits = UART_STOP_BITS_1,
        .flow_ctrl = UART_HW_FLOWCTRL_DISABLE,
        .rx_flow_ctrl_thresh = 122,   // Default threshold value (can be adjusted)
        .source_clk = UART_SCLK_DEFAULT,
        .flags = 0
    };

    uart_param_config(RD03D_UART_PORT, &uart_config);
    uart_set_pin(RD03D_UART_PORT, RD03D_TX_PIN, RD03D_RX_PIN, UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE);

    if (is_single_target) {
        uart_driver_install(RD03D_UART_PORT, RD03D_BUF_SIZE, 0, 0, NULL, 0);
        // Send single-target detection mode command
        uint8_t cmd[12] = {0xFD, 0xFC, 0xFB, 0xFA, 0x02, 0x00, 0x80, 0x00, 0x04, 0x03, 0x02, 0x01};
        uart_write_bytes(RD03D_UART_PORT, (const char *)cmd, sizeof(cmd));
        ESP_LOGI(RADAR_TAG, "Single-target detection mode activated.");
    } else {
        uart_driver_install(RD03D_UART_PORT, RD03D_BUF_SIZE * 2, 0, 0, NULL, 0);
        // Send multi-target detection mode command
        uint8_t cmd[12] = {0xFD, 0xFC, 0xFB, 0xFA, 0x02, 0x00, 0x90, 0x00, 0x04, 0x03, 0x02, 0x01};
        uart_write_bytes(RD03D_UART_PORT, (const char *)cmd, sizeof(cmd));
        ESP_LOGI(RADAR_TAG, "Multi-target detection mode activated.");
    }

    vTaskDelay(pdMS_TO_TICKS(200));
}

void parse_target(const uint8_t* buf)
{
    // Parse the target 1
    if (buf[0] != 0x00 && buf[1] != 0x00) {
        is_target1_updated = true;
        target1_x = (buf[0] | (buf[1] << 8)) - 0x200;
        target1_y = (buf[2] | (buf[3] << 8)) - 0x8000;
        target1_speed = (buf[4] | (buf[5] << 8)) - 0x10;
        target1_dist_res = (buf[6] | (buf[7] << 8));
        ESP_LOGI(RADAR_TAG, "Target 1 - X: %.2f, Y: %.2f, Speed: %.2f, Distance Res: %d", 
                 target1_x, target1_y, target1_speed, target1_dist_res);
    } else {
        is_target1_updated = false;
    }
    // Parse the target 2
    if (buf[8] != 0x00 && buf[9] != 0x00) {
        is_target2_updated = true;
        target2_x = (buf[8] | (buf[9] << 8)) - 0x200;
        target2_y = (buf[10] | (buf[11] << 8)) - 0x8000;
        target2_speed = (buf[12] | (buf[13] << 8)) - 0x10;
        target2_dist_res = (buf[14] | (buf[15] << 8));
        ESP_LOGI(RADAR_TAG, "Target 2 - X: %.2f, Y: %.2f, Speed: %.2f, Distance Res: %d", 
                 target2_x, target2_y, target2_speed, target2_dist_res);
    } else {
        is_target2_updated = false;
    }
    // Parse the target 3
    if (buf[16] != 0x00 && buf[17] != 0x00) {
        is_target3_updated = true;
        target3_x = (buf[16] | (buf[17] << 8)) - 0x200;
        target3_y = (buf[18] | (buf[19] << 8)) - 0x8000;
        target3_speed = (buf[20] | (buf[21] << 8)) - 0x10;
        target3_dist_res = (buf[22] | (buf[23] << 8));
        ESP_LOGI(RADAR_TAG, "Target 3 - X: %.2f, Y: %.2f, Speed: %.2f, Distance Res: %d", 
                 target3_x, target3_y, target3_speed, target3_dist_res);
    } else {
        is_target3_updated = false;
    }
}

void rd03d_read_single_target() {
    size_t rx_len = 0;
    memset(radar_rx_buf, 0x00, sizeof(radar_rx_buf));
    
    uart_get_buffered_data_len(RD03D_UART_PORT, &rx_len);

    if (rx_len > 0) {
        rx_len = uart_read_bytes(RD03D_UART_PORT, radar_rx_buf, sizeof(radar_rx_buf), pdMS_TO_TICKS(10));

        // Check for header
        if (rx_len >= 32) {
            if ((radar_rx_buf[0] == 0xAA) && (radar_rx_buf[1] == 0xFF)) {
                target1_x = (radar_rx_buf[4] | (radar_rx_buf[5] << 8)) - 0x200;
                target1_y = (radar_rx_buf[6] | (radar_rx_buf[7] << 8)) - 0x8000;
                target1_speed = (radar_rx_buf[8] | (radar_rx_buf[9] << 8)) - 0x10;
                target1_dist_res = (radar_rx_buf[10] | (radar_rx_buf[11] << 8));
                
                ESP_LOGI(RADAR_TAG, "Target 1 - X: %.2f, Y: %.2f, Speed: %.2f, Distance Res: %d", 
                    target1_x, target1_y, target1_speed, target1_dist_res);
            }
        }
        else {
            target1_x = 0;
            target1_y = 0;
            target1_speed = 0;
            target1_dist_res = 0;
        }
    }
}

void rd03d_read_multiple_target() {
    uint8_t data[RD03D_BUF_SIZE];
    int len = uart_read_bytes(RD03D_UART_PORT, data, RD03D_BUF_SIZE, 20 / portTICK_PERIOD_MS);
    if (len > 0) {
        // Check for header
        for (int i = 0; i < len - 6; i++) {
            if (data[i] == 0xAA && data[i+1] == 0xFF && data[i+2] == 0x03 && data[i+3] == 0x00) {
                // Check for tail
                for (int j = i + 4; j < len - 1; j++) {
                    if (data[j] == 0x55 && data[j+1] == 0xCC) {
                        int frame_len = j + 2 - i;
                        const uint8_t* frame = &data[i + 4];
                        parse_target(frame);
                        i = j+1;  // Skip to end of frame
                        break;
                    }
                }
            }
        }
    }
}

#endif
