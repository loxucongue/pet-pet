<script setup>
/** 上传体检报告页面。 */
import { computed, ref } from "vue";
import { onLoad, onUnload } from "@dcloudio/uni-app";

import EmptyState from "@/components/EmptyState.vue";
import LoadingOverlay from "@/components/LoadingOverlay.vue";
import PetSwitcher from "@/components/PetSwitcher.vue";
import { analyzeHealthReport, getHealthQuota } from "@/api/health.js";
import { getPetList } from "@/api/pet.js";
import { buildApiUrl, getAuthHeaders, resolveFileUrl } from "@/utils/request.js";

const loading = ref(false);
const analyzing = ref(false);
const petList = ref([]);
const currentPetId = ref(null);
const initialPetId = ref(null);
const quotaRemaining = ref(0);
const selectedFile = ref(null);
const analyzingText = ref("正在准备分析...");

let analyzingTimer = null;

const canAnalyze = computed(() => {
  if (quotaRemaining.value <= 0) {
    return false;
  }

  return Boolean(currentPetId.value && selectedFile.value?.localPath && !analyzing.value);
});

const analyzeButtonClass = computed(() => (canAnalyze.value ? "btn-primary" : "btn-disabled"));

function goBack() {
  if (getCurrentPages().length > 1) {
    uni.navigateBack({ delta: 1 });
    return;
  }

  uni.switchTab({
    url: "/pages/ai/index",
  });
}

async function initializePage() {
  loading.value = true;
  try {
    const [petResponse, quotaResponse] = await Promise.all([
      getPetList(undefined, { showLoading: false }),
      getHealthQuota({ showLoading: false }),
    ]);

    petList.value = petResponse?.items || [];
    quotaRemaining.value = Number(quotaResponse?.remaining || 0);

    if (!petList.value.length) {
      currentPetId.value = null;
      return;
    }

    const matchedPet = petList.value.find((item) => item.id === initialPetId.value);
    currentPetId.value = matchedPet?.id || petList.value[0].id;
  } catch (error) {
    petList.value = [];
    currentPetId.value = null;
    quotaRemaining.value = 0;
  } finally {
    loading.value = false;
  }
}

function handlePetChange(petId) {
  if (!petId) {
    openAddPetPage();
    return;
  }

  currentPetId.value = petId;
}

function openAddPetPage() {
  uni.navigateTo({
    url: "/pages/pet/add",
  });
}

function chooseImage(sourceType) {
  return new Promise((resolve, reject) => {
    uni.chooseImage({
      count: 1,
      sizeType: ["compressed"],
      sourceType,
      success: (result) => {
        const filePath = result.tempFilePaths?.[0] || "";
        resolve({
          localPath: filePath,
          fileType: "image",
          name: filePath.split("/").pop() || "report.jpg",
          previewUrl: filePath,
          filePath: "",
          fileUrl: "",
        });
      },
      fail: reject,
    });
  });
}

function choosePdfFile() {
  return new Promise((resolve, reject) => {
    if (typeof uni.chooseMessageFile !== "function") {
      reject(new Error("当前端暂不支持 PDF 文件选择，请先用图片方式预览。"));
      return;
    }

    uni.chooseMessageFile({
      count: 1,
      type: "file",
      extension: ["pdf"],
      success: (result) => {
        const file = result.tempFiles?.[0] || result.files?.[0] || {};
        const filePath = file.path || result.tempFilePaths?.[0] || "";

        resolve({
          localPath: filePath,
          fileType: "pdf",
          name: file.name || filePath.split("/").pop() || "report.pdf",
          previewUrl: "",
          filePath: "",
          fileUrl: "",
        });
      },
      fail: reject,
    });
  });
}

async function handleSelectFile() {
  const tapIndex = await new Promise((resolve) => {
    uni.showActionSheet({
      itemList: ["拍照上传", "相册选图", "选择 PDF 文件"],
      success: (result) => resolve(result.tapIndex),
      fail: () => resolve(-1),
    });
  });

  if (tapIndex < 0) {
    return;
  }

  try {
    if (tapIndex === 0) {
      selectedFile.value = await chooseImage(["camera"]);
      return;
    }

    if (tapIndex === 1) {
      selectedFile.value = await chooseImage(["album"]);
      return;
    }

    selectedFile.value = await choosePdfFile();
  } catch (error) {
    if (error?.errMsg?.includes("cancel")) {
      return;
    }

    uni.showToast({
      title: error.message || "选择文件失败",
      icon: "none",
    });
  }
}

function uploadReportFile(fileInfo) {
  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url: buildApiUrl("/api/upload/report"),
      filePath: fileInfo.localPath,
      name: "file",
      header: getAuthHeaders({}, false),
      success: (result) => {
        let responseData = {};

        try {
          responseData = JSON.parse(result.data || "{}");
        } catch (error) {
          reject(error);
          return;
        }

        if (result.statusCode >= 200 && result.statusCode < 300) {
          resolve(responseData);
          return;
        }

        reject(new Error(responseData.detail || responseData.message || "报告上传失败"));
      },
      fail: reject,
    });
  });
}

function startAnalyzingAnimation() {
  const texts = ["正在上传报告...", "正在识别体检内容...", "正在生成通俗解读..."];
  let cursor = 0;
  analyzingText.value = texts[cursor];

  stopAnalyzingAnimation();
  analyzingTimer = setInterval(() => {
    cursor = (cursor + 1) % texts.length;
    analyzingText.value = texts[cursor];
  }, 1400);
}

function stopAnalyzingAnimation() {
  if (analyzingTimer) {
    clearInterval(analyzingTimer);
    analyzingTimer = null;
  }
}

async function refreshQuota() {
  try {
    const quotaResponse = await getHealthQuota({ showLoading: false });
    quotaRemaining.value = Number(quotaResponse?.remaining || 0);
  } catch (error) {
    // Ignore quota refresh errors.
  }
}

async function handleAnalyze() {
  if (!canAnalyze.value) {
    if (quotaRemaining.value <= 0) {
      uni.showToast({
        title: "AI 分析次数已用完",
        icon: "none",
      });
    }
    return;
  }

  analyzing.value = true;
  startAnalyzingAnimation();

  try {
    let reportFilePath = selectedFile.value.filePath;
    let reportFileUrl = selectedFile.value.fileUrl;

    if (!reportFilePath) {
      const uploadResult = await uploadReportFile(selectedFile.value);
      reportFilePath = uploadResult.file_path || "";
      reportFileUrl = uploadResult.file_url || resolveFileUrl(reportFilePath);
      selectedFile.value = {
        ...selectedFile.value,
        filePath: reportFilePath,
        fileUrl: reportFileUrl,
      };
    }

    const report = await analyzeHealthReport(
      {
        pet_id: currentPetId.value,
        file_path: reportFilePath,
        file_type: selectedFile.value.fileType,
      },
      { showLoading: false },
    );

    await refreshQuota();

    uni.showToast({
      title: "分析完成",
      icon: "success",
    });

    setTimeout(() => {
      uni.redirectTo({
        url: `/pages/ai/report-detail?reportId=${report.id}`,
      });
    }, 320);
  } catch (error) {
    await refreshQuota();
    if (String(error?.message || "").includes("上传")) {
      uni.showToast({
        title: error.message || "报告分析失败",
        icon: "none",
      });
    }
  } finally {
    analyzing.value = false;
    stopAnalyzingAnimation();
  }
}

onLoad((options) => {
  const petId = Number(options?.petId || 0);
  if (petId) {
    initialPetId.value = petId;
  }
  initializePage();
});

onUnload(() => {
  stopAnalyzingAnimation();
});
</script>

<template>
  <view class="upload-page">
    <LoadingOverlay :visible="loading || analyzing" :text="analyzing ? analyzingText : '正在加载宠物和额度...'" />

    <scroll-view scroll-y class="upload-page__scroll">
      <view class="page-shell upload-page__shell">
        <view class="upload-page__topbar">
          <view class="upload-page__back" @click="goBack">‹</view>
          <view class="tag-soft">体检分析</view>
        </view>

        <view class="upload-page__hero">
          <text class="section-title">上传体检报告</text>
          <text class="section-caption">
            先选择宠物，再上传图片或 PDF 文件。分析完成后会自动归档到历史记录中。
          </text>
        </view>

        <view v-if="petList.length" class="page-content">
          <view class="card">
            <view class="upload-page__section-head">
              <text class="upload-page__section-title">选择宠物</text>
              <view
                class="upload-page__quota-pill"
                :class="{ 'upload-page__quota-pill--danger': quotaRemaining <= 0 }"
              >
                {{ quotaRemaining > 0 ? `剩余 ${quotaRemaining} 次` : "次数已用完" }}
              </view>
            </view>
            <PetSwitcher :pet-list="petList" :current-pet-id="currentPetId" @change="handlePetChange" />
          </view>

          <view class="card upload-page__picker-card">
            <view class="upload-page__section-head">
              <view>
                <text class="upload-page__section-title">上传报告</text>
                <text class="section-caption">支持拍照、相册图片和 PDF 文件。</text>
              </view>
              <view class="tag-soft">单次 1 份</view>
            </view>

            <view class="upload-page__picker-box" @click="handleSelectFile">
              <template v-if="selectedFile">
                <image
                  v-if="selectedFile.fileType === 'image'"
                  class="upload-page__preview-image"
                  :src="selectedFile.previewUrl || selectedFile.fileUrl"
                  mode="aspectFill"
                />
                <view v-else class="upload-page__file-preview">
                  <text class="upload-page__file-icon">PDF</text>
                  <text class="upload-page__file-name">{{ selectedFile.name }}</text>
                </view>
                <text class="upload-page__change-tip">点击重新选择</text>
              </template>
              <template v-else>
                <view class="upload-page__picker-placeholder">
                  <text class="upload-page__upload-icon">＋</text>
                  <text class="upload-page__upload-title">上传报告文件</text>
                  <text class="section-caption">拍照上传更适合单页图片，PDF 适合整份体检报告。</text>
                </view>
              </template>
            </view>
          </view>

          <view class="card upload-page__tips-card">
            <text class="upload-page__section-title">分析说明</text>
            <view class="upload-page__tip-list">
              <text class="upload-page__tip-item">1. 上传后会先做 OCR 识别，再生成通俗化解读。</text>
              <text class="upload-page__tip-item">2. 分析失败不会扣减次数，识别成功的记录会自动进入历史列表。</text>
              <text class="upload-page__tip-item">3. 若剩余次数不足，按钮会自动置灰。</text>
            </view>
          </view>
        </view>

        <view v-else class="card">
          <EmptyState
            icon="🐱"
            text="开始上传报告前，需要先添加一只宠物。"
            button-text="添加宠物"
            @action="openAddPetPage"
          />
        </view>
      </view>
    </scroll-view>

    <view class="upload-page__footer">
      <text class="upload-page__footer-text">
        {{ quotaRemaining > 0 ? "确认文件后开始分析，分析完成会自动跳转结果页。" : "当前剩余次数为 0，请稍后再试。" }}
      </text>
      <view :class="analyzeButtonClass" @click="handleAnalyze">
        {{ analyzing ? "分析中..." : "开始分析" }}
      </view>
    </view>
  </view>
</template>

<style scoped lang="scss">
.upload-page {
  min-height: 100vh;
  padding-bottom: 188rpx;
}

.upload-page__scroll {
  height: 100vh;
}

.upload-page__shell {
  gap: 24rpx;
}

.upload-page__topbar,
.upload-page__section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.upload-page__back {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56rpx;
  height: 56rpx;
  border-radius: 50%;
  color: var(--text-primary);
  font-size: 40rpx;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: var(--shadow-card);
}

.upload-page__hero {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.upload-page__section-title {
  color: var(--text-primary);
  font-size: 30rpx;
  font-weight: 700;
}

.upload-page__quota-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 48rpx;
  padding: 0 18rpx;
  border-radius: 999rpx;
  color: var(--color-primary);
  font-size: var(--font-mini);
  background: rgba(255, 198, 211, 0.45);
}

.upload-page__quota-pill--danger {
  color: var(--color-danger);
  background: rgba(255, 107, 107, 0.14);
}

.upload-page__picker-card,
.upload-page__tips-card {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.upload-page__picker-box {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 360rpx;
  padding: 28rpx;
  border: 2rpx dashed rgba(255, 139, 167, 0.36);
  border-radius: 32rpx;
  background: linear-gradient(180deg, rgba(255, 247, 250, 0.92) 0%, rgba(247, 251, 255, 0.96) 100%);
}

.upload-page__picker-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12rpx;
  text-align: center;
}

.upload-page__upload-icon {
  color: var(--color-primary);
  font-size: 60rpx;
  line-height: 1;
}

.upload-page__upload-title,
.upload-page__file-name {
  color: var(--text-primary);
  font-size: 30rpx;
  font-weight: 700;
}

.upload-page__preview-image {
  width: 100%;
  height: 304rpx;
  border-radius: 26rpx;
}

.upload-page__file-preview {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 18rpx;
}

.upload-page__file-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 120rpx;
  height: 120rpx;
  border-radius: 30rpx;
  color: #ffffff;
  font-size: 34rpx;
  font-weight: 700;
  background: linear-gradient(135deg, #ff8ba7 0%, #a8d8ea 100%);
}

.upload-page__change-tip {
  margin-top: 18rpx;
  color: var(--text-secondary);
  font-size: var(--font-mini);
}

.upload-page__tip-list {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.upload-page__tip-item {
  color: var(--text-secondary);
  font-size: var(--font-caption);
  line-height: 1.6;
}

.upload-page__footer {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  gap: 14rpx;
  padding: 18rpx 24rpx 34rpx;
  background: rgba(255, 253, 254, 0.96);
  box-shadow: 0 -12rpx 28rpx rgba(255, 195, 211, 0.14);
  backdrop-filter: blur(10px);
}

.upload-page__footer-text {
  color: var(--text-secondary);
  font-size: var(--font-mini);
  line-height: 1.5;
}
</style>
