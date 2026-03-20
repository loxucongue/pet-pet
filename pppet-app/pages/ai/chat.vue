<script setup>
/** AI 对话页面。 */
import { computed, nextTick, ref } from "vue";
import { onLoad, onShow, onUnload } from "@dcloudio/uni-app";

import EmptyState from "@/components/EmptyState.vue";
import LoadingOverlay from "@/components/LoadingOverlay.vue";
import {
  createChatSession,
  getChatPermissions,
  getChatQuota,
  getChatSessionMessages,
  getChatSessions,
  streamChatMessage,
} from "@/api/chat.js";
import { getPetDetail } from "@/api/pet.js";
import { resolveFileUrl } from "@/utils/request.js";
import { getUserInfo } from "@/utils/storage.js";

let localMessageSeed = 0;
let activeStreamTask = null;
let typingQueue = "";
let typingTimer = null;
let typingWaiters = [];

const loading = ref(false);
const sessionReady = ref(false);
const sending = ref(false);
const petId = ref(null);
const sessionId = ref(null);
const shouldForceNewSession = ref(false);
const petInfo = ref(null);
const quotaRemaining = ref(null);
const messageList = ref([]);
const inputText = ref("");
const scrollAnchorId = ref("");
const currentUser = ref(getUserInfo() || null);

const petAvatarUrl = computed(() => resolveFileUrl(petInfo.value?.avatar));
const pageTitle = computed(() => `${petInfo.value?.nickname || "宠物"}的专属顾问`);
const userAvatarText = computed(() => currentUser.value?.nickname?.slice(0, 1) || "我");
const quotaHintText = computed(() => {
  if (quotaRemaining.value === null) {
    return "今日剩余 不限";
  }

  if (quotaRemaining.value <= 0) {
    return "今日次数已用完";
  }

  return `今日剩余 ${quotaRemaining.value} 次`;
});
const isInputDisabled = computed(() => !sessionReady.value || sending.value || quotaRemaining.value === 0);
const inputPlaceholder = computed(() =>
  quotaRemaining.value === 0 ? "今日对话次数已用完" : "输入你想咨询的问题...",
);
const sendButtonLabel = computed(() => (sending.value ? "发送中" : "发送"));

const displayMessages = computed(() =>
  messageList.value.map((message, index) => ({
    ...message,
    anchorId: `chat-message-${message.id || message.localId || index}`,
  })),
);

function buildLocalMessage(role, content = "") {
  localMessageSeed += 1;
  return {
    localId: `local-${role}-${localMessageSeed}`,
    role,
    content,
    created_at: new Date().toISOString(),
    streaming: role === "assistant",
  };
}

function formatErrorMessage(error) {
  if (!error) {
    return "AI 对话暂时不可用，请稍后重试。";
  }

  if (typeof error === "string") {
    return error;
  }

  return error.message || error.detail || "AI 对话暂时不可用，请稍后重试。";
}

function normalizeMessages(items = []) {
  return items.map((item) => ({
    id: item.id,
    role: item.role,
    content: item.content || "",
    created_at: item.created_at,
    streaming: false,
  }));
}

function getStreamingAssistantMessage() {
  const reversed = messageList.value.slice().reverse();
  return reversed.find((item) => item.role === "assistant" && item.streaming);
}

function scheduleScrollToBottom() {
  nextTick(() => {
    const lastMessage = displayMessages.value[displayMessages.value.length - 1];
    if (lastMessage?.anchorId) {
      scrollAnchorId.value = "";
      nextTick(() => {
        scrollAnchorId.value = lastMessage.anchorId;
      });
    }
  });
}

function resolveTypingWaiters() {
  const waiters = typingWaiters.slice();
  typingWaiters = [];
  waiters.forEach((resolve) => resolve());
}

function flushTypingState() {
  if (typingTimer) {
    clearInterval(typingTimer);
    typingTimer = null;
  }
  typingQueue = "";
  resolveTypingWaiters();
}

function waitForTypingDrain() {
  if (!typingQueue && !typingTimer) {
    return Promise.resolve();
  }

  return new Promise((resolve) => {
    typingWaiters.push(resolve);
  });
}

function startTypingTimer() {
  if (typingTimer || !typingQueue) {
    return;
  }

  typingTimer = setInterval(() => {
    const streamingMessage = getStreamingAssistantMessage();
    if (!streamingMessage) {
      flushTypingState();
      return;
    }

    if (!typingQueue) {
      clearInterval(typingTimer);
      typingTimer = null;
      resolveTypingWaiters();
      return;
    }

    const nextLength = Math.min(2, typingQueue.length);
    const nextText = typingQueue.slice(0, nextLength);
    typingQueue = typingQueue.slice(nextLength);
    streamingMessage.content += nextText;
    messageList.value = [...messageList.value];
    scheduleScrollToBottom();
  }, 22);
}

function appendAssistantChunk(chunk, replaceContent = false) {
  const streamingMessage = getStreamingAssistantMessage();
  if (!streamingMessage) {
    return;
  }

  if (replaceContent) {
    streamingMessage.content = "";
    typingQueue = String(chunk || "");
  } else {
    typingQueue += String(chunk || "");
  }

  messageList.value = [...messageList.value];
  startTypingTimer();
}

async function fetchMessages() {
  if (!sessionId.value) {
    return;
  }

  const response = await getChatSessionMessages(
    sessionId.value,
    {
      page: 1,
      page_size: 100,
    },
    {
      showLoading: false,
    },
  );

  messageList.value = normalizeMessages(response?.items || []);
  scheduleScrollToBottom();
}

async function initializeSession() {
  if (!petId.value) {
    uni.showToast({
      title: "缺少宠物信息",
      icon: "none",
    });
    return;
  }

  loading.value = true;
  sessionReady.value = false;

  try {
    const [petResponse, quotaResponse, permissionResponse, sessionResponse] = await Promise.all([
      getPetDetail(petId.value, { showLoading: false }),
      getChatQuota({ showLoading: false }),
      getChatPermissions({ showLoading: false }),
      getChatSessions(
        {
          pet_id: petId.value,
        },
        { showLoading: false },
      ),
    ]);

    const permissionItem = (permissionResponse?.items || []).find((item) => item.pet_id === petId.value);
    if (!permissionItem) {
      throw new Error("未找到该宠物的对话权限信息。");
    }

    if (permissionItem.is_locked && !permissionItem.has_session && !sessionId.value && !shouldForceNewSession.value) {
      uni.showModal({
        title: "暂未解锁",
        content: permissionItem.lock_reason || "当前宠物还不能开启 AI 对话。",
        showCancel: false,
        confirmText: "我知道了",
        confirmColor: "#FF8BA7",
      });
      goBack();
      return;
    }

    petInfo.value = petResponse || null;
    quotaRemaining.value = quotaResponse?.remaining ?? null;

    const sessions = sessionResponse?.items || [];
    if (shouldForceNewSession.value) {
      const newSession = await createChatSession(
        {
          pet_id: petId.value,
        },
        {
          showLoading: false,
        },
      );
      sessionId.value = newSession.id;
      shouldForceNewSession.value = false;
    } else if (!sessionId.value) {
      sessionId.value = sessions[0]?.id || null;
    }

    if (!sessionId.value) {
      const newSession = await createChatSession(
        {
          pet_id: petId.value,
        },
        {
          showLoading: false,
        },
      );
      sessionId.value = newSession.id;
    }

    await fetchMessages();
    sessionReady.value = true;
  } catch (error) {
    sessionReady.value = false;
    messageList.value = [];
    uni.showToast({
      title: formatErrorMessage(error),
      icon: "none",
    });
  } finally {
    loading.value = false;
  }
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

function openHistoryPage() {
  if (!petId.value) {
    return;
  }

  uni.navigateTo({
    url: `/pages/ai/chat-history?petId=${petId.value}`,
  });
}

async function finalizeStreamSuccess(payload = {}) {
  sending.value = false;
  if (payload.remaining !== undefined) {
    quotaRemaining.value = payload.remaining;
  }
  await waitForTypingDrain();
  await fetchMessages();
}

async function finalizeStreamError(error) {
  sending.value = false;
  await waitForTypingDrain();
  await fetchMessages();

  uni.showToast({
    title: formatErrorMessage(error),
    icon: "none",
  });
}

async function handleSend() {
  const content = inputText.value.trim();
  if (!content || sending.value || !sessionReady.value || quotaRemaining.value === 0) {
    return;
  }

  const knownMessageCount = messageList.value.length;
  const userMessage = buildLocalMessage("user", content);
  const assistantMessage = buildLocalMessage("assistant", "");

  inputText.value = "";
  sending.value = true;
  typingQueue = "";
  messageList.value = [...messageList.value, userMessage, assistantMessage];
  scheduleScrollToBottom();

  activeStreamTask?.cancel?.();
  activeStreamTask = streamChatMessage(
    sessionId.value,
    content,
    {
      onStart(payload) {
        if (payload?.session_id) {
          sessionId.value = payload.session_id;
        }
      },
      onMessage(chunk, replaceContent = false) {
        appendAssistantChunk(chunk, replaceContent);
      },
      onDone(payload) {
        finalizeStreamSuccess(payload);
      },
      onError(error) {
        finalizeStreamError(error);
      },
    },
    {
      knownMessageCount,
    },
  );

  try {
    await activeStreamTask.promise;
  } catch (error) {
    // Error toast is handled in finalizeStreamError.
  }
}

onLoad((options) => {
  const nextPetId = Number(options?.petId || 0);
  const nextSessionId = Number(options?.sessionId || 0);
  const forceNewSessionFlag = String(options?.newSession || "") === "1";

  if (nextPetId) {
    petId.value = nextPetId;
  }

  if (nextSessionId) {
    sessionId.value = nextSessionId;
  }

  shouldForceNewSession.value = forceNewSessionFlag;
});

onShow(() => {
  initializeSession();
});

onUnload(() => {
  activeStreamTask?.cancel?.();
  flushTypingState();
});
</script>

<template>
  <view class="chat-page">
    <LoadingOverlay :visible="loading" text="正在加载 AI 对话..." />

    <view class="page-shell chat-page__shell">
      <view class="chat-page__topbar">
        <view class="chat-page__back" @click="goBack">←</view>

        <view class="chat-page__pet-card">
          <view class="chat-page__pet-avatar">
            <image v-if="petAvatarUrl" :src="petAvatarUrl" mode="aspectFill" />
            <text v-else>{{ petInfo?.nickname?.slice(0, 1) || "宠" }}</text>
          </view>
          <view class="chat-page__pet-copy">
            <text class="chat-page__pet-title">{{ pageTitle }}</text>
            <text class="chat-page__pet-desc">已加载宠物档案、近期健康记录和历史对话上下文。</text>
          </view>
        </view>

        <view class="chat-page__history-btn" @click="openHistoryPage">历史</view>
      </view>

      <view class="chat-page__notice">
        AI 建议仅供参考，不能替代专业兽医诊断，紧急情况请立即就医。
      </view>

      <scroll-view
        scroll-y
        class="chat-page__messages"
        :scroll-into-view="scrollAnchorId"
        scroll-with-animation
      >
        <view v-if="displayMessages.length" class="chat-page__message-list">
          <view
            v-for="message in displayMessages"
            :id="message.anchorId"
            :key="message.anchorId"
            class="chat-page__message-row"
            :class="{
              'chat-page__message-row--user': message.role === 'user',
              'chat-page__message-row--assistant': message.role === 'assistant',
            }"
          >
            <view v-if="message.role === 'assistant'" class="chat-page__avatar chat-page__avatar--assistant">
              <text>AI</text>
            </view>

            <view class="chat-page__bubble-wrap">
              <view
                class="chat-page__bubble"
                :class="{
                  'chat-page__bubble--assistant': message.role === 'assistant',
                  'chat-page__bubble--user': message.role === 'user',
                }"
              >
                <text class="chat-page__bubble-text">{{ message.content }}</text>
                <text v-if="message.streaming" class="chat-page__typing-cursor">▌</text>
              </view>
            </view>

            <view v-if="message.role === 'user'" class="chat-page__avatar chat-page__avatar--user">
              <text>{{ userAvatarText }}</text>
            </view>
          </view>
        </view>

        <view v-else class="chat-page__empty">
          <EmptyState
            icon="💬"
            text="先描述你想咨询的问题。AI 会结合宠物档案和近期健康记录来回答。"
          />
        </view>
      </scroll-view>

      <view class="chat-page__composer">
        <view class="chat-page__quota-row">
          <text class="chat-page__quota-text">{{ quotaHintText }}</text>
          <text class="chat-page__quota-sub">
            {{ quotaRemaining === null ? "会员不限" : "发送后会自动扣减 1 次" }}
          </text>
        </view>

        <view class="chat-page__input-shell" :class="{ 'chat-page__input-shell--disabled': quotaRemaining === 0 }">
          <input
            v-model="inputText"
            class="chat-page__input"
            :disabled="isInputDisabled"
            :placeholder="inputPlaceholder"
            maxlength="4000"
            confirm-type="send"
            @confirm="handleSend"
          />

          <view
            class="chat-page__send-btn"
            :class="{
              'chat-page__send-btn--loading': sending,
              'chat-page__send-btn--disabled': !inputText.trim() || isInputDisabled,
            }"
            @click="handleSend"
          >
            <view v-if="sending" class="chat-page__send-spinner" />
            <text>{{ sendButtonLabel }}</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<style scoped lang="scss">
.chat-page {
  min-height: 100vh;
}

.chat-page__shell {
  display: flex;
  height: 100vh;
  flex-direction: column;
  gap: 20rpx;
  padding-bottom: 24rpx;
}

.chat-page__topbar {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.chat-page__back,
.chat-page__history-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  height: 56rpx;
  border-radius: 999rpx;
  font-size: var(--font-caption);
  box-shadow: var(--shadow-card);
}

.chat-page__back {
  width: 56rpx;
  color: var(--text-primary);
  font-size: 34rpx;
  background: rgba(255, 255, 255, 0.92);
}

.chat-page__history-btn {
  min-width: 88rpx;
  padding: 0 18rpx;
  color: var(--color-primary);
  background: linear-gradient(90deg, rgba(255, 198, 211, 0.55) 0%, rgba(212, 240, 247, 0.72) 100%);
}

.chat-page__pet-card {
  display: flex;
  flex: 1;
  min-width: 0;
  align-items: center;
  gap: 14rpx;
}

.chat-page__pet-avatar,
.chat-page__avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border-radius: 50%;
}

.chat-page__pet-avatar {
  width: 68rpx;
  height: 68rpx;
  flex-shrink: 0;
  color: #ffffff;
  font-size: 26rpx;
  font-weight: 700;
  background: linear-gradient(180deg, rgba(255, 198, 211, 0.82) 0%, rgba(168, 216, 234, 0.92) 100%);
}

.chat-page__pet-avatar image {
  width: 100%;
  height: 100%;
}

.chat-page__pet-copy {
  display: flex;
  flex: 1;
  min-width: 0;
  flex-direction: column;
  gap: 6rpx;
}

.chat-page__pet-title {
  color: var(--text-primary);
  font-size: 30rpx;
  font-weight: 700;
}

.chat-page__pet-desc {
  color: var(--text-secondary);
  font-size: var(--font-mini);
  line-height: 1.4;
}

.chat-page__notice {
  padding: 18rpx 20rpx;
  border-radius: 24rpx;
  color: #8f6d25;
  font-size: var(--font-mini);
  line-height: 1.5;
  background: rgba(255, 243, 208, 0.96);
  border: 2rpx solid rgba(245, 200, 66, 0.18);
}

.chat-page__messages {
  flex: 1;
  min-height: 0;
}

.chat-page__message-list {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
  padding: 8rpx 0 12rpx;
}

.chat-page__message-row {
  display: flex;
  align-items: flex-end;
  gap: 12rpx;
}

.chat-page__message-row--user {
  justify-content: flex-end;
}

.chat-page__message-row--assistant {
  justify-content: flex-start;
}

.chat-page__avatar {
  width: 56rpx;
  height: 56rpx;
  flex-shrink: 0;
  font-size: var(--font-mini);
  font-weight: 700;
}

.chat-page__avatar--assistant {
  color: #ffffff;
  background: linear-gradient(180deg, rgba(255, 198, 211, 0.92) 0%, rgba(212, 240, 247, 0.95) 100%);
}

.chat-page__avatar--user {
  color: #ffffff;
  background: linear-gradient(180deg, rgba(255, 163, 187, 0.94) 0%, rgba(159, 197, 255, 0.95) 100%);
}

.chat-page__bubble-wrap {
  display: flex;
  max-width: calc(100% - 68rpx);
}

.chat-page__bubble {
  display: inline-flex;
  align-items: flex-end;
  gap: 4rpx;
  padding: 18rpx 20rpx;
  border-radius: 28rpx;
  word-break: break-word;
}

.chat-page__bubble--assistant {
  background: rgba(255, 255, 255, 0.96);
  border: 2rpx solid rgba(232, 230, 236, 1);
}

.chat-page__bubble--user {
  color: #ffffff;
  background: linear-gradient(90deg, rgba(255, 163, 187, 1) 0%, rgba(159, 197, 255, 1) 100%);
}

.chat-page__bubble-text {
  color: inherit;
  font-size: var(--font-caption);
  line-height: 1.65;
  white-space: pre-wrap;
}

.chat-page__typing-cursor {
  color: var(--color-primary);
  font-size: 22rpx;
  animation: chat-blink 1s ease infinite;
}

.chat-page__empty {
  padding-top: 80rpx;
}

.chat-page__composer {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
  padding: 12rpx 0 0;
}

.chat-page__quota-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.chat-page__quota-text,
.chat-page__quota-sub {
  color: var(--text-secondary);
  font-size: var(--font-mini);
}

.chat-page__quota-text {
  color: #7f7886;
  font-weight: 600;
}

.chat-page__input-shell {
  display: flex;
  align-items: center;
  gap: 12rpx;
  padding: 10rpx;
  border-radius: 30rpx;
  background: rgba(255, 255, 255, 0.96);
  border: 2rpx solid rgba(236, 232, 239, 1);
}

.chat-page__input-shell--disabled {
  opacity: 0.72;
}

.chat-page__input {
  flex: 1;
  min-width: 0;
  min-height: 44rpx;
  padding: 0 12rpx;
  color: var(--text-primary);
  font-size: var(--font-body);
}

.chat-page__send-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
  min-width: 116rpx;
  height: 72rpx;
  padding: 0 20rpx;
  border-radius: 999rpx;
  color: #ffffff;
  font-size: var(--font-caption);
  font-weight: 600;
  background: linear-gradient(90deg, var(--color-primary) 0%, var(--color-secondary) 100%);
}

.chat-page__send-btn--disabled {
  background: var(--color-disabled);
}

.chat-page__send-btn--loading {
  opacity: 0.92;
}

.chat-page__send-spinner {
  width: 24rpx;
  height: 24rpx;
  border: 4rpx solid rgba(255, 255, 255, 0.35);
  border-top-color: #ffffff;
  border-radius: 50%;
  animation: chat-rotate 0.8s linear infinite;
}

@keyframes chat-blink {
  0%,
  100% {
    opacity: 1;
  }

  50% {
    opacity: 0.2;
  }
}

@keyframes chat-rotate {
  from {
    transform: rotate(0deg);
  }

  to {
    transform: rotate(360deg);
  }
}
</style>
