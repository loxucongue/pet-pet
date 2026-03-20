<script setup>
/** 记录页占位页面。 */
import EmptyState from "@/components/EmptyState.vue";
</script>

<template>
  <view class="page-shell">
    <view class="page-content">
      <view class="card">
        <text class="section-title">记录</text>
        <text class="section-caption">后续会放体重、护理、消费和医疗记录时间线。</text>
      </view>
      <view class="card">
        <EmptyState icon="📝" text="记录模块页面占位，后续接入真实数据。" button-text="去添加记录" />
      </view>
    </view>
  </view>
</template>
