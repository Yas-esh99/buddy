
#include "driver/gpio.h"
#include "esp_err.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "driver/i2s_std.h"
#include "inttypes.h"
#include "freertos/ringbuf.h"
#include "ring_buf.h"

i2s_chan_handle_t rx_handle;
const char *TAG = "audio_capture";

void i2s_init(){

  i2s_chan_config_t i2s_chan_cfg = I2S_CHANNEL_DEFAULT_CONFIG(I2S_NUM_AUTO,I2S_ROLE_MASTER);

  ESP_ERROR_CHECK(i2s_new_channel(&i2s_chan_cfg, NULL, &rx_handle));

  i2s_std_config_t i2s_std_cfg = {
    .clk_cfg = I2S_STD_CLK_DEFAULT_CONFIG(16000),
    .slot_cfg = I2S_STD_PHILIPS_SLOT_DEFAULT_CONFIG(I2S_DATA_BIT_WIDTH_32BIT,I2S_SLOT_MODE_MONO),
    .gpio_cfg = {
      .mclk = I2S_GPIO_UNUSED,
      .bclk = GPIO_NUM_14,
      .ws = GPIO_NUM_15,
      .dout = I2S_GPIO_UNUSED,
      .din = GPIO_NUM_32,
      .invert_flags = {
        .mclk_inv = false,
        .bclk_inv = false,
        .ws_inv = false
      }
    }

  };

  ESP_ERROR_CHECK(i2s_channel_init_std_mode(rx_handle,&i2s_std_cfg));
  i2s_channel_enable(rx_handle);


}

void i2s_task(void *arg){

  int32_t *raw_buf = malloc(128 * sizeof(int32_t));
  int16_t *cov_buf = malloc(128 * sizeof(int16_t));
  size_t bytes_read = 0;

  if (!raw_buf || !cov_buf)
  {
    ESP_LOGI(TAG,"Failed to create i2s transfer buffer");
    vTaskDelete(NULL);
  }

  while (1)
  {
    if (i2s_channel_read(rx_handle,raw_buf,128 * sizeof(int32_t),&bytes_read,portMAX_DELAY) == ESP_OK)
    {
      int samples = bytes_read / 4;

      for (int i = 0; i < samples; i++)
      {
        int32_t sample = (int32_t)raw_buf[i];
        cov_buf[i] = __builtin_bswap16((int16_t)(sample >> 16));
      }
      
      size_t size_to_send = samples * sizeof(int16_t);

      BaseType_t res = xRingbufferSend(ring_buffer,cov_buf,size_to_send,0);

      if (res != pdTRUE)
      {
        ESP_LOGW(TAG,"Audio buffer full! droppint frames");
      }
      
    }
    
    
  }

}