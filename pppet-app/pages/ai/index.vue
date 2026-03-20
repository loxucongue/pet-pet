<script setup>
/** AI 页占位页面。 */
import EmptyState from "@/components/EmptyState.vue";
</script>

<template>
  <view class="page-shell">
    <view class="page-content">
      <view class="card">
        <text class="section-title">AI 助手</text>
        <text class="section-caption">这里会承接体检报告分析与日常问答。</text>
      </view>
      <view class="card">
        <EmptyState icon="🤖" text="AI 模块占位中，后续接入对话与分析能力。" button-text="查看报告" />
      </view>
    </view>
  </view>
</template>
