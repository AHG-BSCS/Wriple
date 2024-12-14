#ifndef ESP32_CSI_TIME_COMPONENT_H
#define ESP32_CSI_TIME_COMPONENT_H

#include <sys/time.h>

static char *SET_TIMESTAMP_SIMPLE_TEMPLATE = (char *) "%li.%li";
static char *SET_TIMESTAMP_TEMPLATE = (char *) "SETTIME: %li.%li";

bool real_time_set = false;

bool match_set_timestamp_template(char *candidate_string) {
    long int tv_sec;
    long int tv_usec;
    return sscanf(candidate_string, SET_TIMESTAMP_TEMPLATE, &tv_sec, &tv_usec) > 0;
}

void time_set(char *timestamp_string) {
    long int tv_sec;
    long int tv_usec;

    int res = sscanf(timestamp_string, SET_TIMESTAMP_TEMPLATE, &tv_sec, &tv_usec);
    if (res <= 0) {
        res = sscanf(timestamp_string, SET_TIMESTAMP_SIMPLE_TEMPLATE, &tv_sec, &tv_usec);
    }

    if (res > 0) {
        struct timeval now = {.tv_sec = tv_sec, .tv_usec = tv_usec};
        settimeofday(&now, NULL);
        real_time_set = true;
    }
}

double get_system_clock_timestamp() {
    struct timeval now;
    gettimeofday(&now, NULL);
    return now.tv_sec + now.tv_usec / 1000000.0;
}

double get_steady_clock_timestamp() {
    struct timespec now;
    clock_gettime(CLOCK_MONOTONIC, &now);
    return now.tv_sec + now.tv_nsec / 1000000000.0;
}

#endif //ESP32_CSI_TIME_COMPONENT_H
