<script setup>
/** 社区页占位页面。 */
import EmptyState from "@/components/EmptyState.vue";
</script>

<template>
  <view class="page-shell">
    <view class="page-content">
      <view class="card">
        <text class="section-title">社区</text>
        <text class="section-caption">这里会展示生活类、训化类和医疗类内容。</text>
      </view>
      <view class="card">
        <EmptyState icon="💬" text="社区页面占位中，后续接入文章和互动流。" button-text="去看看" />
      </view>
    </view>
  </view>
</template>
