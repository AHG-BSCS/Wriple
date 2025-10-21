#ifndef SERVER_COMPONENT_H
#define SERVER_COMPONENT_H

#include "globals.cc"

#define SERVER_TAG "SERVER"
#define SERVER_PORT 5001

static char rx_buffer[64];
extern int server_sock;
static struct sockaddr_in broadcast_addr;
extern struct sockaddr_in server_addr;
static uint16_t prev_server_port = 0;
extern socklen_t server_addr_len;

void socket_init() {
    server_sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (server_sock < 0) {
        ESP_LOGE(SERVER_TAG, "Socket failed: errno=%d", errno);
        server_sock = -1;
        return;
    }

    broadcast_addr.sin_family = AF_INET;
    broadcast_addr.sin_port = htons(SERVER_PORT);
    broadcast_addr.sin_addr.s_addr = htonl(INADDR_ANY);

    if (bind(server_sock, (struct sockaddr *)&broadcast_addr, sizeof(broadcast_addr)) < 0) {
        ESP_LOGE(SERVER_TAG, "Bind failed: errno=%d", errno);
        close(server_sock);
        server_sock = -1;
        return;
    }

    struct timeval tv;
    tv.tv_sec = 0;
    tv.tv_usec = 500000; // 500 ms
    setsockopt(server_sock, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));
}

void discover_server_address() {
    if (server_sock == -1) socket_init();
    if (server_sock == -1) {
        ESP_LOGE(SERVER_TAG, "Socket not ready. Aborting server discovery.");
        return;
    }

    while (1) {
        // Get the address of the connected server
        ESP_LOGI(SERVER_TAG, "Listening for server broadcast...");
        int len = recvfrom(server_sock, rx_buffer, sizeof(rx_buffer)-1, 0,
                           (struct sockaddr *)&server_addr, &server_addr_len);

        if (len > 0) {
            rx_buffer[len] = 0; // Null-terminate whatever is received
            if (strcmp(rx_buffer, "Broadcast") == 0) {
                uint16_t server_port = ntohs(server_addr.sin_port);
                if (server_port != prev_server_port) {
                    // Reply to let server trace new ESP32 IP address
                    sendto(server_sock, "", 0, 0, (struct sockaddr *)&server_addr, server_addr_len);
                }
                ESP_LOGI(SERVER_TAG, "Server discovered: IP=%s Port=%d",
                         inet_ntoa(server_addr.sin_addr), ntohs(server_addr.sin_port));
                return;
            }
        }
        else if (prev_server_port != 0) return;
    }
}

#endif
