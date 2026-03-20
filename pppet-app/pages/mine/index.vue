<script setup>
/** 我的页页面，提供宠物管理入口。 */

function goPetList() {
  uni.navigateTo({
    url: "/pages/pet/list",
  });
}
</script>

<template>
  <view class="page-shell">
    <view class="page-content">
      <view class="card">
        <text class="section-title">我的</text>
        <text class="section-caption">这里会承接宠物管理、会员权益和设置。</text>
      </view>
      <view class="card">
        <text class="mine-entry__title">宠物档案管理</text>
        <text class="section-caption">从这里进入宠物管理列表，可查看所有宠物、编辑信息或新增毛孩子。</text>
        <view class="mine-entry__panel" @click="goPetList">
          <view class="mine-entry__icon">🐾</view>
          <view class="mine-entry__copy">
            <text class="mine-entry__name">我的毛孩子</text>
            <text class="mine-entry__desc">进入宠物管理列表</text>
          </view>
          <text class="mine-entry__arrow">›</text>
        </view>
        <view class="btn-primary mine-entry__button" @click="goPetList">管理宠物档案</view>
      </view>
    </view>
  </view>
</template>

<style scoped lang="scss">
.mine-entry__title {
  display: block;
  margin-bottom: 12rpx;
  color: var(--text-primary);
  font-size: 30rpx;
  font-weight: 700;
}

.mine-entry__panel {
  display: flex;
  align-items: center;
  gap: 20rpx;
  margin-top: 24rpx;
  padding: 24rpx;
  border-radius: 28rpx;
  background: linear-gradient(90deg, rgba(255, 233, 240, 0.9) 0%, rgba(235, 244, 255, 0.95) 100%);
}

.mine-entry__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 92rpx;
  height: 92rpx;
  border-radius: 50%;
  font-size: 40rpx;
  background: rgba(255, 255, 255, 0.8);
}

.mine-entry__copy {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 8rpx;
}

.mine-entry__name {
  color: var(--text-primary);
  font-size: 30rpx;
  font-weight: 700;
}

.mine-entry__desc {
  color: var(--text-secondary);
  font-size: var(--font-caption);
}

.mine-entry__arrow {
  color: var(--text-secondary);
  font-size: 36rpx;
}

.mine-entry__button {
  margin-top: 24rpx;
}
</style>
