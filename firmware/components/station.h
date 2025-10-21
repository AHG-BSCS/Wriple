#ifndef STATION_COMPONENT_H
#define STATION_COMPONENT_H

#define STATION_TAG "STATION"

#define STA_SSID "WRIPLE"
#define STA_PASS "WRIPLE_ESP32"

static void wifi_event_handler(void* arg, esp_event_base_t event_base,
                          int32_t event_id, void* event_data) {
    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_START) {
        esp_wifi_connect();
        ESP_LOGI(STATION_TAG, "Station Mode Active");
    } else if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_DISCONNECTED) {
        // ESP_LOGI(STATION_TAG, "Reconnecting to the AP");
        // esp_wifi_connect();
        esp_restart();
    } else if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_CONNECTED) {
        ESP_LOGI(STATION_TAG, "Connected to the AP");
    }
}

static void station_init() {
    ESP_ERROR_CHECK(esp_netif_init());

    ESP_ERROR_CHECK(esp_event_loop_create_default());
    esp_netif_create_default_wifi_sta();

    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    ESP_ERROR_CHECK(esp_wifi_init(&cfg));

    esp_event_handler_instance_t instance_any_id;
    ESP_ERROR_CHECK(esp_event_handler_instance_register(WIFI_EVENT, ESP_EVENT_ANY_ID,
                    &wifi_event_handler, NULL, &instance_any_id));

    wifi_config_t wifi_config = {};
    strlcpy((char *) wifi_config.sta.ssid, STA_SSID, sizeof(STA_SSID));
    strlcpy((char *) wifi_config.sta.password, STA_PASS, sizeof(STA_PASS));

    ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
    ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wifi_config));
    ESP_ERROR_CHECK(esp_wifi_start());

    ESP_ERROR_CHECK(esp_wifi_set_ps(WIFI_PS_NONE));

    ESP_LOGI(STATION_TAG, "Connecting: SSID=%s Password=%s", STA_SSID, STA_PASS);
}

#endif
