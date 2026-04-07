#include "ring_buf.h"
#include "esp_log.h"

#include "freertos/ringbuf.h"

static const char *TAG = "ring_buf";

RingbufHandle_t ring_buffer = NULL;

void ring_buffer_init(void) {
  ring_buffer = xRingbufferCreate(8 * 1024, RINGBUF_TYPE_BYTEBUF);

  if (ring_buffer == NULL) {
    ESP_LOGE(TAG, "Failed to create ring buffer");
  } else {
    ESP_LOGI(TAG, "Ring buffer created successfully");
  }
}