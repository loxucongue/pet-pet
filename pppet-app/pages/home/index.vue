<script setup>
/** 临时首页，用于验证前端初始化和后端联通。 */
import { ref } from "vue";

import { mockLogin } from "@/api/auth.js";
import EmptyState from "@/components/EmptyState.vue";
import LoadingOverlay from "@/components/LoadingOverlay.vue";
import PetSwitcher from "@/components/PetSwitcher.vue";
import { getToken, setToken, setUserInfo } from "@/utils/storage.js";

const currentPetId = ref(1);
const loadingVisible = ref(false);
const testResult = ref("");
const petList = ref([
  { id: 1, nickname: "小橘", emoji: "🐱" },
  { id: 2, nickname: "米粒", emoji: "🐶" },
  { id: 3, nickname: "雪球", emoji: "🐹" },
]);

function handlePetChange(petId) {
  currentPetId.value = petId;
}

function toggleLoading() {
  loadingVisible.value = !loadingVisible.value;
}

async function handleMockLoginTest() {
  try {
    loadingVisible.value = true;
    const response = await mockLogin("H5联调测试用户");
    setToken(response.access_token);
    setUserInfo(response.user);
    testResult.value = `token 已写入本地存储，当前用户：${response.user.nickname}`;
    console.log("mock-login result", response);
    console.log("local token", getToken());
    uni.showToast({
      title: "接口测试成功",
      icon: "success",
    });
  } finally {
    loadingVisible.value = false;
  }
}
</script>

<template>
  <view class="page-shell">
    <view class="page-content">
      <view class="card">
        <text class="section-title">pppet</text>
        <text class="section-caption">
          项目初始化成功。这里既保留了样式基座，也作为 H5 联调时的临时首页。
        </text>
        <view class="demo-actions">
          <view class="btn-primary" @click="handleMockLoginTest">测试接口</view>
        </view>
        <text v-if="testResult" class="home-result">{{ testResult }}</text>
      </view>

      <view class="card">
        <text class="section-title demo-title">PetSwitcher</text>
        <PetSwitcher :pet-list="petList" :current-pet-id="currentPetId" @change="handlePetChange" />
      </view>

      <view class="card">
        <text class="section-title demo-title">基础控件</text>
        <input class="input-field" placeholder="输入框样式示例" placeholder-class="demo-placeholder" />
        <view class="demo-actions">
          <view class="btn-primary" @click="toggleLoading">显示加载遮罩</view>
          <view class="btn-secondary">次按钮</view>
        </view>
      </view>

      <view class="card">
        <text class="section-title demo-title">EmptyState</text>
        <EmptyState icon="🐾" text="这里还没有宠物日记，去记录今天的小事吧。" button-text="去添加记录" />
      </view>
    </view>

    <LoadingOverlay :visible="loadingVisible" text="正在温柔整理宠物数据..." />
  </view>
</template>

<style scoped lang="scss">
.demo-title {
  display: block;
  margin-bottom: 24rpx;
}

.demo-actions {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
  margin-top: 24rpx;
}

.demo-placeholder {
  color: #cccccc;
}

.home-result {
  display: block;
  margin-top: 20rpx;
  color: var(--color-primary);
  font-size: var(--font-caption);
  line-height: 1.5;
}
</style>
