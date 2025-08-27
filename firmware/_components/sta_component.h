#ifndef ESP32_STA_COMPONENT_H
#define ESP32_STA_COMPONENT_H

#include "lwip/sockets.h"
#include "lwip/netdb.h"

#define STA_TAG "STATION"

#define STA_PORT 5001

char rx_buffer[64];
static int rx_sock = -1;
struct sockaddr_in client_addr;
struct sockaddr_in server_addr;

static uint16_t prev_client_port = 0;

void setup_server_address() {
    rx_sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(STA_PORT);
    server_addr.sin_addr.s_addr = htonl(INADDR_ANY);
    bind(rx_sock, (struct sockaddr *)&server_addr, sizeof(server_addr));
}

void get_station_ip_address() {
    if (rx_sock == -1) setup_server_address();
    socklen_t addr_len = sizeof(client_addr);

    while (1) {
        // Get the IP address of the connected station
        int len = recvfrom(rx_sock, rx_buffer, sizeof(rx_buffer)-1, 0,
                           (struct sockaddr *)&client_addr, &addr_len);

        if (len > 0) {
            rx_buffer[len] = 0; // Null-terminate whatever is received
            if (strcmp(rx_buffer, "Connect") == 0) {
                uint16_t client_port = ntohs(client_addr.sin_port);
                if (client_port != prev_client_port) {
                    // Reply to let station trace the ESP32 IP address only when port changes
                    sendto(rx_sock, "", 0, 0, (struct sockaddr *)&client_addr, addr_len);
                }
                ESP_LOGI(STA_TAG, "Station IP: %s PORT: %d",
                         inet_ntoa(client_addr.sin_addr), ntohs(client_addr.sin_port));
                return;
            }
        }
    }
}

#endif
