#include "esp_log.h"
#include "esp_mac.h"
#include "esp_timer.h"
#include "esp_wifi.h"
#include "nvs_flash.h"

#include "../_components/csi_component.h"

#define ESP_WIFI_SSID   CONFIG_ESP_WIFI_SSID
#define ESP_WIFI_PASS   CONFIG_ESP_WIFI_PASSWORD
// #define WIFI_CHANNEL    CONFIG_ESP_WIFI_CHANNEL
#define WIFI_CHANNEL    6
#define MAX_STA_CONN    CONFIG_ESP_MAX_STA_CONN


// #ifdef CONFIG_WIFI_CHANNEL
// #define WIFI_CHANNEL CONFIG_WIFI_CHANNEL
// #else
// #define WIFI_CHANNEL 6
// #endif

#define MAIN_TAG "MAIN"

/* FreeRTOS event group to signal when we are connected*/
static EventGroupHandle_t s_wifi_event_group;

/* The event group allows multiple bits for each event, but we only care about one event
 * - are we connected to the AP with an IP? */
const int WIFI_CONNECTED_BIT = BIT0;

static void event_handler(void* arg, esp_event_base_t event_base,
                          int32_t event_id, void* event_data) {
    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_START) {
        esp_wifi_connect();
        ESP_LOGI(MAIN_TAG, "Connected to the AP");
    } else if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_DISCONNECTED) {
        ESP_LOGI(MAIN_TAG, "Reconnecting to the AP");
        esp_wifi_connect();
        xEventGroupClearBits(s_wifi_event_group, WIFI_CONNECTED_BIT);
    }
}

void nvs_init() {
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);
}

void config_print() {
    printf("\n\n");
    printf("-----------------------\n");
    printf("ESP32 CSI Tool Settings\n");
    printf("-----------------------\n");
    printf("PROJECT_NAME: %s\n", "Wriple");
    printf("CONFIG_ESPTOOLPY_MONITOR_BAUD: %d\n", CONFIG_ESPTOOLPY_MONITOR_BAUD);
    printf("CONFIG_ESP_CONSOLE_UART_BAUDRATE: %d\n", CONFIG_ESP_CONSOLE_UART_BAUDRATE);
    printf("-----------------------\n");
    printf("WIFI_CHANNEL: %d\n", WIFI_CHANNEL);
    printf("ESP_WIFI_SSID: %s\n", ESP_WIFI_SSID);
    printf("ESP_WIFI_PASSWORD: %s\n", ESP_WIFI_PASS);
    printf("-----------------------\n");
    printf("\n\n");
}

void station_init() {
    s_wifi_event_group = xEventGroupCreate();

    ESP_ERROR_CHECK(esp_netif_init());

    ESP_ERROR_CHECK(esp_event_loop_create_default());
    esp_netif_create_default_wifi_sta();

    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));

    esp_event_handler_instance_t instance_any_id;
    ESP_ERROR_CHECK(esp_event_handler_instance_register(WIFI_EVENT,
                                                        ESP_EVENT_ANY_ID,
                                                        &event_handler,
                                                        NULL,
                                                        &instance_any_id));

    wifi_sta_config_t wifi_sta_config = {};
    // wifi_sta_config.channel = WIFI_CHANNEL;
    wifi_config_t wifi_config = {
        .sta = wifi_sta_config
    };

    strlcpy((char *) wifi_config.sta.ssid, ESP_WIFI_SSID, sizeof(ESP_WIFI_SSID));
    strlcpy((char *) wifi_config.sta.password, ESP_WIFI_PASS, sizeof(ESP_WIFI_PASS));

    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wifi_config));
    ESP_ERROR_CHECK(esp_wifi_start());

    esp_wifi_set_ps(WIFI_PS_NONE);

    ESP_LOGI(MAIN_TAG, "Connecting to SSID:%s Password:%s", ESP_WIFI_SSID, ESP_WIFI_PASS);
}

extern "C" void app_main() {
    nvs_init();
    config_print();
    station_init();

    // Add a delay for sensor to initialize
    vTaskDelay(pdMS_TO_TICKS(1000));
    rd03d_init();
    ld2420_init();
    csi_init();
}
