<script>
/** 全局应用入口。 */
export default {
  onLaunch() {
    // 预留 token 校验逻辑：
    // 1. 读取本地 token
    // 2. 校验登录状态是否有效
    // 3. 根据结果决定进入首页或登录页
  },
  onShow() {},
  onHide() {},
};
</script>

<style lang="scss">
@import "@/uni.scss";

:root,
page {
  --color-primary: #{$color-primary};
  --color-primary-light: #{$color-primary-light};
  --color-secondary: #{$color-secondary};
  --color-secondary-light: #{$color-secondary-light};
  --bg-page: #{$bg-page};
  --bg-card: #{$bg-card};
  --text-primary: #{$text-primary};
  --text-secondary: #{$text-secondary};
  --text-placeholder: #{$text-placeholder};
  --color-success: #{$color-success};
  --color-warning: #{$color-warning};
  --color-danger: #{$color-danger};
  --color-disabled: #{$color-disabled};
  --radius-sm: #{$radius-sm};
  --radius-md: #{$radius-md};
  --radius-lg: #{$radius-lg};
  --radius-full: #{$radius-full};
  --shadow-card: #{$shadow-card};
  --font-title: #{$font-title};
  --font-body: #{$font-body};
  --font-caption: #{$font-caption};
  --font-mini: #{$font-mini};
  --color-border-soft: #f4dfe7;
}

page {
  min-height: 100%;
  background: var(--bg-page);
  color: var(--text-primary);
  font-size: var(--font-body);
}

view,
text,
button,
input,
textarea,
scroll-view,
image,
swiper,
swiper-item {
  box-sizing: border-box;
}

button {
  margin: 0;
  padding: 0;
  line-height: 1;
  border: 0;
  background: transparent;
}

button::after {
  border: 0;
}

.page-shell {
  min-height: 100vh;
  padding: 32rpx 24rpx 40rpx;
  background: var(--bg-page);
}

.page-content {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.card {
  padding: 28rpx;
  background: var(--bg-card);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
}

.btn-primary,
.btn-secondary,
.btn-disabled {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 88rpx;
  padding: 0 32rpx;
  border-radius: 999rpx;
  font-size: var(--font-body);
  font-weight: 600;
}

.btn-primary {
  color: #ffffff;
  background: linear-gradient(90deg, var(--color-primary) 0%, var(--color-secondary) 100%);
  box-shadow: 0 12rpx 24rpx rgba(255, 139, 167, 0.18);
}

.btn-secondary {
  color: var(--color-primary);
  background: #ffffff;
  border: 2rpx solid var(--color-primary-light);
}

.btn-disabled {
  color: #ffffff;
  background: var(--color-disabled);
}

.input-field {
  width: 100%;
  min-height: 88rpx;
  padding: 0 28rpx;
  background: #fff8fa;
  border: 2rpx solid transparent;
  border-radius: var(--radius-md);
  color: var(--text-primary);
  font-size: var(--font-body);
}

.input-field.is-textarea {
  min-height: 180rpx;
  padding-top: 24rpx;
  padding-bottom: 24rpx;
}

.input-field.is-focus {
  border-color: var(--color-primary-light);
}

.section-title {
  color: var(--text-primary);
  font-size: var(--font-title);
  font-weight: 700;
  line-height: 1.3;
}

.section-caption {
  color: var(--text-secondary);
  font-size: var(--font-caption);
  line-height: 1.5;
}

.divider {
  width: 100%;
  height: 2rpx;
  background: rgba(255, 139, 167, 0.12);
}

.tag-soft {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 10rpx 18rpx;
  border-radius: 999rpx;
  color: var(--color-primary);
  font-size: var(--font-mini);
  background: linear-gradient(90deg, rgba(255, 198, 211, 0.55) 0%, rgba(212, 240, 247, 0.7) 100%);
}
</style>
