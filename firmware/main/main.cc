#include "esp_log.h"
#include "nvs_flash.h"
#include "esp_wifi.h"

#include "../components/csi.h"
#include "../components/station.h"

void config_print() {
    printf("\n\n");
    printf("-----------------------\n");
    printf("PROJECT NAME: %s\n", CONFIG_LWIP_LOCAL_HOSTNAME);
    printf("MONITOR BAUDRATE: %d\n", CONFIG_CONSOLE_UART_BAUDRATE);
    printf("CONSOLE BAUDRATE: %d\n", CONFIG_ESP_CONSOLE_UART_BAUDRATE);
    printf("-----------------------\n");
    printf("WIFI SSID: %s\n", STA_SSID);
    printf("WIFI PASSWORD: %s\n", STA_PASS);
    printf("-----------------------\n");
    printf("\n\n");
}

void nvs_init() {
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);
}

extern "C" void app_main() {
    nvs_init();
    config_print();
    station_init();
    esp_log_level_set("wifi", ESP_LOG_ERROR);

    // Wait for AP connection and radar stabilization
    vTaskDelay(pdMS_TO_TICKS(500));
    // Discover server address before initializing CSI and RDM
    socket_init();
    discover_server_address();

    rdm_init();
    csi_init();
}
