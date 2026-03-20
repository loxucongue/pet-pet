<script setup>
/** 登录页，占位并提供 mock 登录入口。 */
import { ref } from "vue";

import { mockLogin } from "@/api/auth.js";
import { setToken, setUserInfo } from "@/utils/storage.js";

const nickname = ref("测试用户");
const submitting = ref(false);

async function handleMockLogin() {
  if (!nickname.value.trim()) {
    uni.showToast({
      title: "请输入昵称",
      icon: "none",
    });
    return;
  }

  submitting.value = true;
  try {
    const response = await mockLogin(nickname.value.trim());
    setToken(response.access_token);
    setUserInfo(response.user);

    uni.showToast({
      title: "登录成功",
      icon: "success",
    });

    setTimeout(() => {
      uni.switchTab({
        url: "/pages/home/index",
      });
    }, 400);
  } finally {
    submitting.value = false;
  }
}
</script>

<template>
  <view class="page-shell">
    <view class="page-content">
      <view class="card login-card">
        <text class="section-title">欢迎来到 pppet</text>
        <text class="section-caption">开发阶段先使用 mock 登录，后续会接入微信登录。</text>

        <view class="login-card__field">
          <text class="login-card__label">昵称</text>
          <input v-model="nickname" class="input-field" placeholder="请输入昵称" />
        </view>

        <view class="btn-primary" @click="handleMockLogin">
          {{ submitting ? "登录中..." : "Mock 登录" }}
        </view>
      </view>
    </view>
  </view>
</template>

<style scoped lang="scss">
.login-card {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
  margin-top: 120rpx;
}

.login-card__field {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.login-card__label {
  color: var(--color-primary);
  font-size: var(--font-caption);
  font-weight: 600;
}
</style>
