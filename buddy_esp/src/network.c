#include "esp_log.h"
#include "esp_random.h"
#include "esp_wifi.h"
#include "freertos/event_groups.h"
#include "freertos/ringbuf.h"
#include "inttypes.h"
#include "lwip/sockets.h"
#include "nvs_flash.h"
#include "ring_buf.h"

#define WIFI_SSID "M01s"
#define WIFI_PASS "9924760032"

#define DEST_IP "255.255.255.255"
#define DEST_PORT 5004

#define SAMPLE_RATE 16000
#define CHUNK_SAMPLE 320
#define RTP_HEADER_SIZE 12

EventGroupHandle_t wifi_event_group;
#define WIFI_CONNECTED_BIT BIT0

static const char *TAG = "network";

static void event_handler(void *arg, esp_event_base_t event_base,
                          int32_t event_id, void *event_data) {
  if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_START) {
    esp_wifi_connect();
  } else if (event_base == IP_EVENT && event_id == IP_EVENT_STA_GOT_IP) {
    xEventGroupSetBits(wifi_event_group, WIFI_CONNECTED_BIT);
  }
}
struct rtp_header {
  uint8_t flags;
  uint8_t payload_ty;
  uint16_t seq;
  uint32_t timestamp;
  uint32_t src_id;
} __attribute__((packed));

void wifi_task(void *pv) {
  xEventGroupWaitBits(wifi_event_group, BIT0, pdFALSE, pdTRUE, portMAX_DELAY);

  uint8_t tx_buffer[RTP_HEADER_SIZE + (CHUNK_SAMPLE * 2)];
  struct rtp_header *rtp = (struct rtp_header *)tx_buffer;

  rtp->flags = 0x80;
  rtp->payload_ty = 11;
  rtp->src_id = esp_random();

  uint16_t seq = 0;
  uint32_t ts = 0;

  struct sockaddr_in dest;
  dest.sin_addr.s_addr = inet_addr(DEST_IP);
  dest.sin_family = AF_INET;
  dest.sin_port = htons(DEST_PORT);

  int sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_IP);
  if (sock < 0) {
    ESP_LOGE(TAG, "Failed to create socket");
    vTaskDelete(NULL);
  }

  int broadcastEnable = 1;
  setsockopt(sock, SOL_SOCKET, SO_BROADCAST, &broadcastEnable,
             sizeof(broadcastEnable));

  ESP_LOGI(TAG, "Stream Starting...");

  while (1) {
    size_t item_size;
    int16_t *pcm_data =
        (int16_t *)xRingbufferReceive(ring_buffer, &item_size, portMAX_DELAY);

    if (!pcm_data)
      continue;

    /* 🔒 SAFETY CHECK */
    if (item_size > CHUNK_SAMPLE * 2) {
      ESP_LOGW(TAG, "PCM chunk too large: %d", item_size);
      vRingbufferReturnItem(ring_buffer, pcm_data);
      continue;
    }

    if (pcm_data != NULL) {
      rtp->seq = htons(seq++);
      rtp->timestamp = htonl(ts);
      ts += item_size / 2;

      memcpy(tx_buffer + RTP_HEADER_SIZE, pcm_data, item_size);

      sendto(sock, tx_buffer, RTP_HEADER_SIZE + item_size, 0,
             (struct sockaddr *)&dest, sizeof(dest));

      vRingbufferReturnItem(ring_buffer, (void *)pcm_data);
    }
  }
}

void wifi_init() {
  esp_err_t ret = nvs_flash_init();
  if (ret == ESP_ERR_NVS_NO_FREE_PAGES ||
      ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
    ESP_ERROR_CHECK(nvs_flash_erase());
    ESP_ERROR_CHECK(nvs_flash_init());
  }

  wifi_event_group = xEventGroupCreate();

  ESP_ERROR_CHECK(esp_netif_init());
  ESP_ERROR_CHECK(esp_event_loop_create_default());

  ESP_ERROR_CHECK(esp_event_handler_register(WIFI_EVENT, ESP_EVENT_ANY_ID,
                                             &event_handler, NULL));
  ESP_ERROR_CHECK(esp_event_handler_register(IP_EVENT, IP_EVENT_STA_GOT_IP,
                                             &event_handler, NULL));

  esp_netif_create_default_wifi_sta();

  wifi_init_config_t wifi_init_cfg = WIFI_INIT_CONFIG_DEFAULT();

  esp_wifi_init(&wifi_init_cfg);

  wifi_config_t wifi_cfg = {.sta = {.ssid = WIFI_SSID, .password = WIFI_PASS}};

  esp_wifi_set_mode(WIFI_MODE_STA);
  esp_wifi_set_config(WIFI_IF_STA, &wifi_cfg);

  esp_wifi_start();

  esp_wifi_set_ps(WIFI_PS_NONE);
}
