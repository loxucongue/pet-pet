<script setup>
/** AI 对话历史页面。 */
import { computed, ref } from "vue";
import { onLoad, onShow } from "@dcloudio/uni-app";

import EmptyState from "@/components/EmptyState.vue";
import LoadingOverlay from "@/components/LoadingOverlay.vue";
import { createChatSession, getChatSessions } from "@/api/chat.js";
import { getPetDetail } from "@/api/pet.js";
import { resolveFileUrl } from "@/utils/request.js";

const loading = ref(false);
const petId = ref(null);
const petInfo = ref(null);
const sessionList = ref([]);

const headerTitle = computed(() => `${petInfo.value?.nickname || "宠物"}的历史会话`);

const historyCards = computed(() =>
  sessionList.value.map((item) => ({
    ...item,
    displayTitle: item.title || "新的健康咨询",
    displayTime: formatDateTime(item.updated_at),
  })),
);

function formatDateTime(value) {
  if (!value) {
    return "";
  }

  const date = new Date(value);
  const today = new Date();
  const sameYear = date.getFullYear() === today.getFullYear();
  const sameMonth = date.getMonth() === today.getMonth();
  const sameDate = date.getDate() === today.getDate();

  const hour = `${date.getHours()}`.padStart(2, "0");
  const minute = `${date.getMinutes()}`.padStart(2, "0");

  if (sameYear && sameMonth && sameDate) {
    return `今天 ${hour}:${minute}`;
  }

  return `${date.getMonth() + 1}-${date.getDate()} ${hour}:${minute}`;
}

function goBack() {
  if (getCurrentPages().length > 1) {
    uni.navigateBack({ delta: 1 });
    return;
  }

  uni.switchTab({
    url: "/pages/ai/index",
  });
}

async function fetchHistoryData() {
  if (!petId.value) {
    return;
  }

  loading.value = true;
  try {
    const [petResponse, sessionResponse] = await Promise.all([
      getPetDetail(petId.value, { showLoading: false }),
      getChatSessions(
        {
          pet_id: petId.value,
        },
        { showLoading: false },
      ),
    ]);

    petInfo.value = {
      ...petResponse,
      avatarUrl: resolveFileUrl(petResponse?.avatar),
    };
    sessionList.value = sessionResponse?.items || [];
  } catch (error) {
    petInfo.value = null;
    sessionList.value = [];
  } finally {
    loading.value = false;
  }
}

function openChat(sessionId) {
  if (!petId.value) {
    return;
  }

  uni.navigateTo({
    url: `/pages/ai/chat?petId=${petId.value}&sessionId=${sessionId}`,
  });
}

async function handleCreateSession() {
  if (!petId.value) {
    return;
  }

  try {
    const session = await createChatSession(
      {
        pet_id: petId.value,
      },
      {
        showLoading: true,
        loadingTitle: "正在创建对话...",
      },
    );

    uni.navigateTo({
      url: `/pages/ai/chat?petId=${petId.value}&sessionId=${session.id}`,
    });
  } catch (error) {
    // Request layer already handles toast.
  }
}

onLoad((options) => {
  const nextPetId = Number(options?.petId || 0);
  if (nextPetId) {
    petId.value = nextPetId;
  }
});

onShow(() => {
  fetchHistoryData();
});
</script>

<template>
  <view class="chat-history-page">
    <LoadingOverlay :visible="loading" text="正在加载历史会话..." />

    <scroll-view scroll-y class="chat-history-page__scroll">
      <view class="page-shell chat-history-page__shell">
        <view class="chat-history-page__topbar">
          <view class="chat-history-page__back" @click="goBack">←</view>
          <view class="btn-secondary chat-history-page__new-btn" @click="handleCreateSession">
            新建对话
          </view>
        </view>

        <view class="chat-history-page__hero">
          <view
            v-if="petInfo"
            class="chat-history-page__pet-avatar"
          >
            <image v-if="petInfo.avatarUrl" :src="petInfo.avatarUrl" mode="aspectFill" />
            <text v-else>{{ petInfo.nickname?.slice(0, 1) || "宠" }}</text>
          </view>
          <view class="chat-history-page__hero-copy">
            <text class="section-title">{{ headerTitle }}</text>
            <text class="section-caption">
              所有对话都会按时间倒序保存，点击卡片即可回到对应上下文继续追问。
            </text>
          </view>
        </view>

        <view v-if="historyCards.length" class="chat-history-page__list">
          <view
            v-for="session in historyCards"
            :key="session.id"
            class="card chat-history-page__item"
            @click="openChat(session.id)"
          >
            <view class="chat-history-page__item-head">
              <text class="chat-history-page__item-title">{{ session.displayTitle }}</text>
              <text class="chat-history-page__item-time">{{ session.displayTime }}</text>
            </view>
            <text class="chat-history-page__item-summary">
              {{ session.last_message_summary || "还没有消息内容，进入后可继续补充这次咨询。" }}
            </text>
            <view class="chat-history-page__item-footer">
              <view class="chat-history-page__count-pill">{{ session.message_count }} 条消息</view>
              <text class="chat-history-page__item-meta">{{ petInfo?.nickname || "宠物" }}</text>
            </view>
          </view>
        </view>

        <view v-else class="card">
          <EmptyState
            icon="💬"
            text="还没有历史会话。新建对话后，这里会保存每次咨询的标题、时间和消息数量。"
            button-text="新建对话"
            @action="handleCreateSession"
          />
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<style scoped lang="scss">
.chat-history-page {
  min-height: 100vh;
}

.chat-history-page__scroll {
  height: 100vh;
}

.chat-history-page__shell {
  gap: 24rpx;
  padding-bottom: 56rpx;
}

.chat-history-page__topbar,
.chat-history-page__item-head,
.chat-history-page__item-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.chat-history-page__back {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56rpx;
  height: 56rpx;
  border-radius: 50%;
  color: var(--text-primary);
  font-size: 34rpx;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: var(--shadow-card);
}

.chat-history-page__new-btn {
  min-width: 0;
  min-height: 64rpx;
  padding: 0 26rpx;
  font-size: var(--font-caption);
}

.chat-history-page__hero {
  display: flex;
  align-items: center;
  gap: 18rpx;
}

.chat-history-page__pet-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 96rpx;
  height: 96rpx;
  overflow: hidden;
  border-radius: 28rpx;
  color: #ffffff;
  font-size: 34rpx;
  font-weight: 700;
  background: linear-gradient(180deg, rgba(255, 198, 211, 0.82) 0%, rgba(168, 216, 234, 0.92) 100%);
}

.chat-history-page__pet-avatar image {
  width: 100%;
  height: 100%;
}

.chat-history-page__hero-copy {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 10rpx;
}

.chat-history-page__list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.chat-history-page__item {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.chat-history-page__item-title {
  flex: 1;
  color: var(--text-primary);
  font-size: 30rpx;
  font-weight: 700;
}

.chat-history-page__item-time,
.chat-history-page__item-meta {
  color: var(--text-secondary);
  font-size: var(--font-mini);
}

.chat-history-page__item-summary {
  color: var(--text-secondary);
  font-size: var(--font-caption);
  line-height: 1.6;
}

.chat-history-page__count-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 44rpx;
  padding: 0 16rpx;
  border-radius: 999rpx;
  color: #8a6071;
  font-size: var(--font-mini);
  background: #fff4f8;
}
</style>
