<script setup>
/** 添加与编辑记录页面。 */
import { computed, reactive, ref } from "vue";
import { onLoad } from "@dcloudio/uni-app";

import LoadingOverlay from "@/components/LoadingOverlay.vue";
import PetSwitcher from "@/components/PetSwitcher.vue";
import { getPetList } from "@/api/pet.js";
import { createRecord, getRecordDetail, updateRecord } from "@/api/record.js";
import { createReminder, deleteReminder, getReminderList, updateReminder } from "@/api/reminder.js";
import {
  RECORD_CATEGORY_OPTIONS,
  getSubTypeOptions,
  isExpenseCategory,
  isWeightSubType,
} from "@/data/record-categories.js";
import { getToday } from "@/utils/date.js";
import { buildApiUrl, getAuthHeaders, resolveFileUrl } from "@/utils/request.js";

const loading = ref(false);
const submitting = ref(false);
const recordId = ref(null);
const initialPetId = ref(null);
const petList = ref([]);
const existingReminderId = ref(null);
const images = ref([]);

const form = reactive({
  pet_id: null,
  record_date: getToday(),
  category: "健康",
  sub_type: "体内驱虫",
  note: "",
  amount: "",
  weight_value: "",
  reminder_enabled: false,
  cycle_days: "30",
  reminder_time: "09:00",
});

const isEditMode = computed(() => Boolean(recordId.value));
const subTypeOptions = computed(() => getSubTypeOptions(form.category));
const showAmountField = computed(() => isExpenseCategory(form.category));
const showWeightField = computed(() => isWeightSubType(form.sub_type));
const pageTitle = computed(() => (isEditMode.value ? "编辑记录" : "添加记录"));

function goBack() {
  if (getCurrentPages().length > 1) {
    uni.navigateBack({ delta: 1 });
    return;
  }

  uni.switchTab({
    url: "/pages/record/index",
  });
}

function openAddPetPage() {
  uni.navigateTo({
    url: "/pages/pet/add",
  });
}

function setCategory(category) {
  form.category = category;
  if (!subTypeOptions.value.includes(form.sub_type)) {
    form.sub_type = subTypeOptions.value[0] || "";
  }
  if (!showAmountField.value) {
    form.amount = "";
  }
}

function setSubType(subType) {
  form.sub_type = subType;
  if (!showWeightField.value) {
    form.weight_value = "";
  }
}

function setPet(petId) {
  if (isEditMode.value) {
    return;
  }
  form.pet_id = petId;
}

function getImageUrl(item) {
  return item.file_url || resolveFileUrl(item.file_path);
}

async function fetchPets() {
  const response = await getPetList(undefined, { showLoading: false });
  petList.value = response?.items || [];

  if (!petList.value.length) {
    form.pet_id = null;
    return;
  }

  const matchedPet =
    petList.value.find((item) => item.id === form.pet_id) ||
    petList.value.find((item) => item.id === initialPetId.value);

  form.pet_id = matchedPet?.id || petList.value[0].id;
}

async function fetchRecordDetailAndReminder() {
  if (!recordId.value) {
    return;
  }

  const record = await getRecordDetail(recordId.value, { showLoading: false });
  form.pet_id = record.pet_id;
  form.record_date = record.record_date;
  form.category = record.category;
  form.sub_type = record.sub_type;
  form.note = record.note || "";
  form.amount = record.amount ?? "";
  form.weight_value = record.weight_value ?? "";
  images.value = (record.images || []).map((item) => ({
    file_path: item.image_path,
    file_url: resolveFileUrl(item.image_path),
  }));

  const reminderList = await getReminderList({ pet_id: record.pet_id }, { showLoading: false });
  const currentReminder = (reminderList || []).find((item) => item.record_id === recordId.value);

  if (currentReminder) {
    existingReminderId.value = currentReminder.id;
    form.reminder_enabled = true;
    form.cycle_days = String(currentReminder.cycle_days);
    form.reminder_time = String(currentReminder.reminder_time || "").slice(0, 5) || "09:00";
  } else {
    existingReminderId.value = null;
    form.reminder_enabled = false;
  }
}

function validateForm() {
  if (!form.pet_id) {
    uni.showToast({ title: "请先选择宠物", icon: "none" });
    return false;
  }

  if (!form.category || !form.sub_type) {
    uni.showToast({ title: "请选择分类和子分类", icon: "none" });
    return false;
  }

  if (showAmountField.value) {
    const amount = Number(form.amount);
    if (!Number.isFinite(amount) || amount <= 0) {
      uni.showToast({ title: "请填写正确的消费金额", icon: "none" });
      return false;
    }
  }

  if (showWeightField.value) {
    const weightValue = Number(form.weight_value);
    if (!Number.isFinite(weightValue) || weightValue <= 0) {
      uni.showToast({ title: "请填写正确的体重数值", icon: "none" });
      return false;
    }
  }

  if (form.reminder_enabled) {
    const cycleDays = Number(form.cycle_days);
    if (!Number.isInteger(cycleDays) || cycleDays <= 0) {
      uni.showToast({ title: "提醒周期需大于 0 天", icon: "none" });
      return false;
    }

    if (!form.reminder_time) {
      uni.showToast({ title: "请选择提醒时间", icon: "none" });
      return false;
    }
  }

  return true;
}

function buildRecordPayload() {
  return {
    pet_id: form.pet_id,
    record_date: form.record_date,
    category: form.category,
    sub_type: form.sub_type,
    note: form.note.trim() || null,
    amount: showAmountField.value ? Number(form.amount) : null,
    weight_value: showWeightField.value ? Number(form.weight_value) : null,
    image_paths: images.value.map((item) => item.file_path),
  };
}

async function syncReminder(savedRecordId) {
  if (form.reminder_enabled) {
    const payload = {
      pet_id: form.pet_id,
      record_id: savedRecordId,
      start_date: form.record_date,
      reminder_type: form.sub_type,
      cycle_days: Number(form.cycle_days),
      reminder_time: form.reminder_time,
      is_active: true,
    };

    if (existingReminderId.value) {
      await updateReminder(existingReminderId.value, payload, { showLoading: false });
    } else {
      const createdReminder = await createReminder(payload, { showLoading: false });
      existingReminderId.value = createdReminder?.id || existingReminderId.value;
    }
    return;
  }

  if (existingReminderId.value) {
    await deleteReminder(existingReminderId.value, { showLoading: false });
    existingReminderId.value = null;
  }
}

function chooseImages() {
  return new Promise((resolve, reject) => {
    uni.chooseImage({
      count: Math.max(1, 9 - images.value.length),
      sizeType: ["compressed"],
      success: resolve,
      fail: reject,
    });
  });
}

function uploadImage(filePath) {
  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url: buildApiUrl("/api/upload/image"),
      filePath,
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

        reject(new Error(responseData.detail || responseData.message || "图片上传失败"));
      },
      fail: reject,
    });
  });
}

async function handleImageUpload() {
  if (images.value.length >= 9) {
    uni.showToast({ title: "最多上传 9 张图片", icon: "none" });
    return;
  }

  try {
    loading.value = true;
    const result = await chooseImages();
    const filePaths = result.tempFilePaths || [];

    for (const filePath of filePaths) {
      const uploadResult = await uploadImage(filePath);
      images.value.push({
        file_path: uploadResult.file_path,
        file_url: uploadResult.file_url || resolveFileUrl(uploadResult.file_path),
      });
    }
  } catch (error) {
    if (!String(error?.errMsg || "").includes("cancel")) {
      uni.showToast({ title: error.message || "图片上传失败", icon: "none" });
    }
  } finally {
    loading.value = false;
  }
}

function removeImage(index) {
  images.value.splice(index, 1);
}

async function handleSubmit() {
  if (!validateForm()) {
    return;
  }

  submitting.value = true;
  try {
    const payload = buildRecordPayload();
    const savedRecord = isEditMode.value
      ? await updateRecord(recordId.value, payload, { showLoading: false })
      : await createRecord(payload, { showLoading: false });

    await syncReminder(savedRecord.id);

    uni.showToast({
      title: isEditMode.value ? "记录已更新" : "记录已添加",
      icon: "success",
    });

    setTimeout(() => {
      uni.redirectTo({
        url: `/pages/record/detail?recordId=${savedRecord.id}`,
      });
    }, 400);
  } finally {
    submitting.value = false;
  }
}

async function initializePage() {
  loading.value = true;
  try {
    await fetchPets();
    await fetchRecordDetailAndReminder();
  } finally {
    loading.value = false;
  }
}

onLoad((options) => {
  const nextRecordId = Number(options?.recordId || 0);
  const nextPetId = Number(options?.petId || 0);

  if (nextRecordId) {
    recordId.value = nextRecordId;
  }

  if (nextPetId) {
    initialPetId.value = nextPetId;
    form.pet_id = nextPetId;
  }

  initializePage();
});
</script>

<template>
  <view class="record-form-page">
    <LoadingOverlay :visible="loading || submitting" :text="submitting ? '正在保存记录...' : '正在准备表单...'" />

    <scroll-view scroll-y class="record-form-page__scroll">
      <view class="page-shell record-form-page__shell">
        <view class="record-form-page__hero">
          <view class="record-form-page__hero-main">
            <view class="record-form-page__back" @click="goBack">‹</view>
            <view>
              <text class="section-title">{{ pageTitle }}</text>
              <text class="section-caption">把当天发生的护理、消费、医疗或体重变化轻轻记下来。</text>
            </view>
          </view>
          <view class="tag-soft">记录中</view>
        </view>

        <view v-if="petList.length" class="page-content">
          <view class="card">
            <view class="record-form-page__section-head">
              <text class="record-form-page__section-title">宠物</text>
              <text class="section-caption">{{ isEditMode ? "编辑模式下宠物归属固定" : "请选择本次记录对应的宠物" }}</text>
            </view>
            <PetSwitcher :pet-list="petList" :current-pet-id="form.pet_id" @change="setPet" />
          </view>

          <view class="card">
            <view class="record-form-page__field">
              <text class="record-form-page__label">记录日期</text>
              <picker mode="date" :value="form.record_date" @change="(event) => (form.record_date = event.detail.value)">
                <view class="input-field record-form-page__picker">
                  <text>{{ form.record_date }}</text>
                  <text>›</text>
                </view>
              </picker>
            </view>

            <view class="record-form-page__field">
              <text class="record-form-page__label">分类</text>
              <view class="record-form-page__chip-list">
                <view
                  v-for="item in RECORD_CATEGORY_OPTIONS"
                  :key="item.key"
                  class="record-form-page__chip"
                  :class="{ 'record-form-page__chip--active': form.category === item.key }"
                  @click="setCategory(item.key)"
                >
                  <text>{{ item.icon }}</text>
                  <text>{{ item.label }}</text>
                </view>
              </view>
            </view>

            <view class="record-form-page__field">
              <text class="record-form-page__label">子分类</text>
              <view class="record-form-page__subtype-list">
                <view
                  v-for="item in subTypeOptions"
                  :key="item"
                  class="record-form-page__subtype"
                  :class="{ 'record-form-page__subtype--active': form.sub_type === item }"
                  @click="setSubType(item)"
                >
                  {{ item }}
                </view>
              </view>
            </view>

            <view class="record-form-page__field">
              <text class="record-form-page__label">备注</text>
              <textarea
                v-model="form.note"
                class="input-field is-textarea"
                maxlength="300"
                placeholder="写下今天发生了什么，方便以后回看。"
              />
            </view>

            <view v-if="showAmountField" class="record-form-page__field">
              <text class="record-form-page__label">消费金额（元）</text>
              <input v-model="form.amount" class="input-field" type="digit" placeholder="例如 89.90" />
            </view>

            <view v-if="showWeightField" class="record-form-page__field">
              <text class="record-form-page__label">体重（kg）</text>
              <input v-model="form.weight_value" class="input-field" type="digit" placeholder="例如 4.75" />
            </view>
          </view>

          <view class="card">
            <view class="record-form-page__section-head">
              <text class="record-form-page__section-title">图片</text>
              <text class="section-caption">最多 9 张，适合放票据、药盒或状态照片</text>
            </view>

            <view class="record-form-page__image-grid">
              <view v-for="(item, index) in images" :key="`${item.file_path}-${index}`" class="record-form-page__image-item">
                <image class="record-form-page__image" :src="getImageUrl(item)" mode="aspectFill" />
                <view class="record-form-page__image-remove" @click="removeImage(index)">×</view>
              </view>
              <view v-if="images.length < 9" class="record-form-page__image-upload" @click="handleImageUpload">
                <text class="record-form-page__image-plus">+</text>
                <text class="record-form-page__image-tip">上传图片</text>
              </view>
            </view>
          </view>

          <view class="card">
            <view class="record-form-page__section-head">
              <text class="record-form-page__section-title">提醒</text>
              <text class="section-caption">保存记录时可顺手创建周期提醒</text>
            </view>

            <view class="record-form-page__switch-row">
              <view>
                <text class="record-form-page__label">开启提醒</text>
                <text class="section-caption">适合驱虫、疫苗、复诊等周期事项</text>
              </view>
              <switch
                :checked="form.reminder_enabled"
                color="#FF8BA7"
                @change="(event) => (form.reminder_enabled = event.detail.value)"
              />
            </view>

            <view v-if="form.reminder_enabled" class="record-form-page__reminder-fields">
              <view class="record-form-page__field">
                <text class="record-form-page__label">周期天数</text>
                <input v-model="form.cycle_days" class="input-field" type="number" placeholder="例如 30" />
              </view>
              <view class="record-form-page__field">
                <text class="record-form-page__label">提醒时间</text>
                <picker mode="time" :value="form.reminder_time" @change="(event) => (form.reminder_time = event.detail.value)">
                  <view class="input-field record-form-page__picker">
                    <text>{{ form.reminder_time }}</text>
                    <text>›</text>
                  </view>
                </picker>
              </view>
            </view>
          </view>
        </view>

        <view v-else class="card">
          <text class="section-caption">你还没有宠物档案，先去添加宠物后再记录。</text>
          <view class="btn-secondary record-form-page__empty-btn" @click="openAddPetPage">
            去添加宠物
          </view>
        </view>
      </view>
    </scroll-view>

    <view class="record-form-page__footer">
      <view class="btn-primary" @click="handleSubmit">
        {{ submitting ? "保存中..." : "保存记录" }}
      </view>
    </view>
  </view>
</template>

<style scoped lang="scss">
.record-form-page {
  min-height: 100vh;
  padding-bottom: 168rpx;
}

.record-form-page__scroll {
  height: 100vh;
}

.record-form-page__shell {
  gap: 24rpx;
}

.record-form-page__hero {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24rpx;
}

.record-form-page__hero-main {
  display: flex;
  align-items: flex-start;
  gap: 16rpx;
}

.record-form-page__back {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56rpx;
  height: 56rpx;
  border-radius: 50%;
  color: var(--text-primary);
  font-size: 36rpx;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: var(--shadow-card);
}

.record-form-page__section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
  margin-bottom: 20rpx;
}

.record-form-page__section-title {
  color: var(--text-primary);
  font-size: 30rpx;
  font-weight: 700;
}

.record-form-page__field {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
  margin-top: 22rpx;
}

.record-form-page__field:first-child {
  margin-top: 0;
}

.record-form-page__label {
  color: var(--text-primary);
  font-size: var(--font-caption);
  font-weight: 600;
}

.record-form-page__picker {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.record-form-page__chip-list,
.record-form-page__subtype-list {
  display: flex;
  flex-wrap: wrap;
  gap: 14rpx;
}

.record-form-page__chip,
.record-form-page__subtype {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
  min-height: 72rpx;
  padding: 0 24rpx;
  border: 2rpx solid transparent;
  border-radius: 999rpx;
  color: var(--text-secondary);
  font-size: var(--font-caption);
  background: #fff8fa;
}

.record-form-page__chip--active,
.record-form-page__subtype--active {
  color: var(--text-primary);
  border-color: rgba(255, 139, 167, 0.35);
  background: linear-gradient(180deg, rgba(255, 198, 211, 0.26) 0%, rgba(212, 240, 247, 0.28) 100%);
}

.record-form-page__image-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16rpx;
}

.record-form-page__image-item,
.record-form-page__image-upload {
  position: relative;
  height: 200rpx;
  overflow: hidden;
  border-radius: 24rpx;
  background: #fff8fa;
}

.record-form-page__image {
  width: 100%;
  height: 100%;
}

.record-form-page__image-remove {
  position: absolute;
  top: 10rpx;
  right: 10rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40rpx;
  height: 40rpx;
  border-radius: 50%;
  color: #ffffff;
  font-size: 26rpx;
  background: rgba(51, 51, 51, 0.52);
}

.record-form-page__image-upload {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
  border: 2rpx dashed rgba(255, 139, 167, 0.28);
}

.record-form-page__image-plus {
  color: var(--color-primary);
  font-size: 44rpx;
}

.record-form-page__image-tip {
  color: var(--text-secondary);
  font-size: var(--font-mini);
}

.record-form-page__switch-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.record-form-page__reminder-fields {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16rpx;
  margin-top: 20rpx;
}

.record-form-page__empty-btn {
  margin-top: 24rpx;
}

.record-form-page__footer {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  padding: 18rpx 24rpx 34rpx;
  background: rgba(255, 253, 254, 0.96);
  box-shadow: 0 -12rpx 28rpx rgba(255, 195, 211, 0.14);
  backdrop-filter: blur(10px);
}
</style>
