<script setup>
/** 宠物添加与编辑页面。 */
import { computed, reactive, ref } from "vue";
import { onLoad } from "@dcloudio/uni-app";

import LoadingOverlay from "@/components/LoadingOverlay.vue";
import petBreedsData from "@/data/pet-breeds.json";
import http, { buildApiUrl, getAuthHeaders, resolveFileUrl } from "@/utils/request.js";

const petId = ref(null);
const loading = ref(false);
const submitting = ref(false);
const avatarPreview = ref("");
const ageMode = ref("birthday");

const speciesOptions = Object.keys(petBreedsData);
const genderOptions = ["公", "母", "未知"];
const neuterOptions = [
  { label: "已绝育", value: true },
  { label: "未绝育", value: false },
  { label: "暂不填写", value: null },
];

const form = reactive({
  avatar: "",
  nickname: "",
  species: "",
  breed: "",
  customBreed: "",
  gender: "",
  birthday: "",
  approximate_age: "",
  weight: "",
  is_neutered: null,
  fur_color: "",
  adoption_date: "",
  allergy_history: "",
  chronic_disease: "",
  current_food_brand: "",
});

const pageTitle = computed(() => (petId.value ? "编辑宠物档案" : "添加宠物档案"));
const breedOptions = computed(() => (form.species ? petBreedsData[form.species] || ["其他"] : []));
const showCustomBreed = computed(() => form.breed === "其他");
const speciesIndex = computed(() => Math.max(speciesOptions.indexOf(form.species), 0));
const breedIndex = computed(() => Math.max(breedOptions.value.indexOf(form.breed), 0));

function trimText(value) {
  return typeof value === "string" ? value.trim() : "";
}

function formatPayload() {
  const finalBreed = showCustomBreed.value ? trimText(form.customBreed) : trimText(form.breed);

  return {
    avatar: form.avatar || null,
    nickname: trimText(form.nickname),
    species: trimText(form.species),
    breed: finalBreed,
    gender: trimText(form.gender) || null,
    birthday: ageMode.value === "birthday" && form.birthday ? form.birthday : null,
    approximate_age:
      ageMode.value === "approximate_age" && trimText(form.approximate_age)
        ? trimText(form.approximate_age)
        : null,
    weight: form.weight ? Number(form.weight) : null,
    is_neutered: form.is_neutered,
    fur_color: trimText(form.fur_color) || null,
    adoption_date: form.adoption_date || null,
    allergy_history: trimText(form.allergy_history) || null,
    chronic_disease: trimText(form.chronic_disease) || null,
    current_food_brand: trimText(form.current_food_brand) || null,
  };
}

function validateForm() {
  const payload = formatPayload();

  if (!payload.nickname) {
    uni.showToast({ title: "请填写宠物昵称", icon: "none" });
    return null;
  }

  if (!payload.species) {
    uni.showToast({ title: "请选择物种", icon: "none" });
    return null;
  }

  if (!payload.breed) {
    uni.showToast({ title: "请选择或填写品种", icon: "none" });
    return null;
  }

  if (payload.weight !== null && (Number.isNaN(payload.weight) || payload.weight <= 0)) {
    uni.showToast({ title: "体重请输入正确数值", icon: "none" });
    return null;
  }

  return payload;
}

function goBack() {
  if (getCurrentPages().length > 1) {
    uni.navigateBack({ delta: 1 });
    return;
  }

  uni.redirectTo({
    url: "/pages/pet/list",
  });
}

function setAgeMode(mode) {
  ageMode.value = mode;
}

function handleSpeciesChange(event) {
  const nextSpecies = speciesOptions[event.detail.value];
  form.species = nextSpecies;

  const nextBreedOptions = petBreedsData[nextSpecies] || ["其他"];
  if (!nextBreedOptions.includes(form.breed)) {
    form.breed = "";
    form.customBreed = "";
  }
}

function handleBreedChange(event) {
  const nextBreed = breedOptions.value[event.detail.value];
  form.breed = nextBreed;
  if (nextBreed !== "其他") {
    form.customBreed = "";
  }
}

function handleDateChange(field, event) {
  form[field] = event.detail.value;
}

function handleGenderChange(value) {
  form.gender = value;
}

function handleNeuterChange(value) {
  form.is_neutered = value;
}

function normalizePetResponse(pet) {
  form.avatar = pet.avatar || "";
  avatarPreview.value = resolveFileUrl(pet.avatar);
  form.nickname = pet.nickname || "";
  form.species = pet.species || "";
  form.breed = pet.breed || "";
  form.customBreed = "";
  form.gender = pet.gender || "";
  form.birthday = pet.birthday || "";
  form.approximate_age = pet.approximate_age || "";
  form.weight = pet.weight === null || pet.weight === undefined ? "" : String(pet.weight);
  form.is_neutered = pet.is_neutered === undefined ? null : pet.is_neutered;
  form.fur_color = pet.fur_color || "";
  form.adoption_date = pet.adoption_date || "";
  form.allergy_history = pet.allergy_history || "";
  form.chronic_disease = pet.chronic_disease || "";
  form.current_food_brand = pet.current_food_brand || "";

  const speciesBreeds = petBreedsData[form.species] || [];
  if (!speciesBreeds.includes(form.breed) && form.breed) {
    form.customBreed = form.breed;
    form.breed = "其他";
  }

  ageMode.value = pet.birthday ? "birthday" : "approximate_age";
}

async function fetchPetDetail() {
  if (!petId.value) {
    return;
  }

  loading.value = true;
  try {
    const pet = await http.get(`/api/pets/${petId.value}`);
    normalizePetResponse(pet);
  } finally {
    loading.value = false;
  }
}

function chooseImage() {
  return new Promise((resolve, reject) => {
    uni.chooseImage({
      count: 1,
      sizeType: ["compressed"],
      success: (result) => {
        resolve(result.tempFilePaths?.[0] || "");
      },
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

        const message = responseData.detail || responseData.message || "头像上传失败";
        reject(new Error(message));
      },
      fail: reject,
    });
  });
}

async function handleAvatarUpload() {
  try {
    const localFilePath = await chooseImage();
    if (!localFilePath) {
      return;
    }

    loading.value = true;
    const uploadResult = await uploadImage(localFilePath);
    form.avatar = uploadResult.file_path || "";
    avatarPreview.value = uploadResult.file_url || resolveFileUrl(uploadResult.file_path);
    uni.showToast({
      title: "头像上传成功",
      icon: "success",
    });
  } catch (error) {
    if (error?.errMsg?.includes("cancel")) {
      return;
    }

    uni.showToast({
      title: error.message || "头像上传失败",
      icon: "none",
    });
  } finally {
    loading.value = false;
  }
}

async function handleSubmit() {
  const payload = validateForm();
  if (!payload) {
    return;
  }

  submitting.value = true;
  try {
    if (petId.value) {
      await http.put(`/api/pets/${petId.value}`, payload);
    } else {
      await http.post("/api/pets", payload);
    }

    uni.showToast({
      title: petId.value ? "保存成功" : "添加成功",
      icon: "success",
    });

    setTimeout(() => {
      uni.redirectTo({
        url: "/pages/pet/list",
      });
    }, 500);
  } finally {
    submitting.value = false;
  }
}

onLoad((options) => {
  const nextPetId = Number(options?.petId || 0);
  if (nextPetId) {
    petId.value = nextPetId;
    fetchPetDetail();
  }
});
</script>

<template>
  <view class="pet-form-page">
    <LoadingOverlay :visible="loading || submitting" :text="submitting ? '正在保存宠物档案...' : '正在加载宠物资料...'" />

    <scroll-view scroll-y class="pet-form-page__scroll">
      <view class="pet-form-page__shell">
        <view class="pet-form-page__header">
          <view class="pet-form-page__topbar">
            <view class="pet-form-page__back" @click="goBack">‹</view>
            <view class="tag-soft">填写中</view>
          </view>
          <text class="pet-form-page__title">{{ pageTitle }}</text>
          <text class="section-caption">带 * 的字段需要填写，我们会把信息整理成温柔好维护的宠物档案。</text>
        </view>

        <view class="card pet-form-page__avatar-card" @click="handleAvatarUpload">
          <view class="pet-form-page__avatar">
            <image v-if="avatarPreview" :src="avatarPreview" mode="aspectFill" />
            <text v-else>🐱</text>
          </view>
          <view class="pet-form-page__avatar-meta">
            <text class="pet-form-page__card-title">宠物头像上传区</text>
            <text class="section-caption">建议上传正面清晰照片，后续头像、记录图片和日记入口都会优先使用这张图。</text>
            <view class="pet-form-page__upload-btn">上传头像</view>
          </view>
        </view>

        <view class="card">
          <view class="pet-form-page__section-head">
            <text class="pet-form-page__card-title">基础信息</text>
            <text class="pet-form-page__required">* 必填</text>
          </view>

          <view class="pet-form-page__field">
            <text class="pet-form-page__label">昵称 *</text>
            <input v-model="form.nickname" class="input-field" placeholder="例如：小橘" />
          </view>

          <view class="pet-form-page__grid">
            <view class="pet-form-page__field pet-form-page__field--half">
              <text class="pet-form-page__label">物种 *</text>
              <picker :range="speciesOptions" :value="speciesIndex" @change="handleSpeciesChange">
                <view class="input-field pet-form-page__picker">
                  <text>{{ form.species || "请选择物种" }}</text>
                  <text class="pet-form-page__arrow">›</text>
                </view>
              </picker>
            </view>

            <view class="pet-form-page__field pet-form-page__field--half">
              <text class="pet-form-page__label">品种 *</text>
              <picker
                :disabled="!breedOptions.length"
                :range="breedOptions"
                :value="breedIndex"
                @change="handleBreedChange"
              >
                <view class="input-field pet-form-page__picker" :class="{ 'pet-form-page__picker--disabled': !breedOptions.length }">
                  <text>{{ form.breed || "请选择品种" }}</text>
                  <text class="pet-form-page__arrow">›</text>
                </view>
              </picker>
            </view>
          </view>

          <view v-if="showCustomBreed" class="pet-form-page__field">
            <text class="pet-form-page__label">手动填写品种 *</text>
            <input v-model="form.customBreed" class="input-field" placeholder="请输入具体品种" />
          </view>

          <view class="pet-form-page__field">
            <text class="pet-form-page__label">性别</text>
            <view class="pet-form-page__segmented">
              <view
                v-for="item in genderOptions"
                :key="item"
                class="pet-form-page__segmented-item"
                :class="{ 'pet-form-page__segmented-item--active': form.gender === item }"
                @click="handleGenderChange(item)"
              >
                {{ item }}
              </view>
            </view>
          </view>
        </view>

        <view class="card">
          <text class="pet-form-page__card-title">成长与状态</text>

          <view class="pet-form-page__age-switch">
            <view
              class="pet-form-page__age-tab"
              :class="{ 'pet-form-page__age-tab--active': ageMode === 'birthday' }"
              @click="setAgeMode('birthday')"
            >
              生日
            </view>
            <view
              class="pet-form-page__age-tab"
              :class="{ 'pet-form-page__age-tab--active': ageMode === 'approximate_age' }"
              @click="setAgeMode('approximate_age')"
            >
              大约年龄
            </view>
          </view>

          <view class="pet-form-page__grid">
            <view class="pet-form-page__field pet-form-page__field--half">
              <text class="pet-form-page__label">{{ ageMode === "birthday" ? "生日" : "大约年龄" }}</text>
              <picker v-if="ageMode === 'birthday'" mode="date" :value="form.birthday" @change="(event) => handleDateChange('birthday', event)">
                <view class="input-field pet-form-page__picker">
                  <text>{{ form.birthday || "请选择生日" }}</text>
                  <text class="pet-form-page__arrow">›</text>
                </view>
              </picker>
              <input
                v-else
                v-model="form.approximate_age"
                class="input-field"
                placeholder="例如：大约 2 岁"
              />
            </view>

            <view class="pet-form-page__field pet-form-page__field--half">
              <text class="pet-form-page__label">体重 kg</text>
              <input v-model="form.weight" class="input-field" type="digit" placeholder="例如：4.5" />
            </view>
          </view>

          <view class="pet-form-page__field">
            <text class="pet-form-page__label">绝育状态</text>
            <view class="pet-form-page__segmented pet-form-page__segmented--three">
              <view
                v-for="item in neuterOptions"
                :key="item.label"
                class="pet-form-page__segmented-item"
                :class="{ 'pet-form-page__segmented-item--active': form.is_neutered === item.value }"
                @click="handleNeuterChange(item.value)"
              >
                {{ item.label }}
              </view>
            </view>
          </view>
        </view>

        <view class="card">
          <text class="pet-form-page__card-title">生活与健康备注</text>

          <view class="pet-form-page__field">
            <text class="pet-form-page__label">毛色</text>
            <input v-model="form.fur_color" class="input-field" placeholder="例如：橘白、三花、奶油色" />
          </view>

          <view class="pet-form-page__field">
            <text class="pet-form-page__label">领养日期</text>
            <picker mode="date" :value="form.adoption_date" @change="(event) => handleDateChange('adoption_date', event)">
              <view class="input-field pet-form-page__picker">
                <text>{{ form.adoption_date || "请选择领养日期" }}</text>
                <text class="pet-form-page__arrow">›</text>
              </view>
            </picker>
          </view>

          <view class="pet-form-page__field">
            <text class="pet-form-page__label">当前主粮品牌</text>
            <input v-model="form.current_food_brand" class="input-field" placeholder="例如：渴望、皇家、鲜朗" />
          </view>

          <view class="pet-form-page__field">
            <text class="pet-form-page__label">过敏史</text>
            <textarea
              v-model="form.allergy_history"
              class="input-field is-textarea"
              maxlength="200"
              placeholder="记录已知过敏食物、药物或环境因素"
            />
          </view>

          <view class="pet-form-page__field">
            <text class="pet-form-page__label">慢性病</text>
            <textarea
              v-model="form.chronic_disease"
              class="input-field is-textarea"
              maxlength="200"
              placeholder="例如：肠胃敏感、心脏问题、皮肤病等"
            />
          </view>
        </view>
      </view>
    </scroll-view>

    <view class="pet-form-page__footer">
      <text class="pet-form-page__footer-hint">保存前自动检查必填项，下滑可继续填写生日、体重和健康信息。</text>
      <view class="btn-primary" @click="handleSubmit">
        {{ submitting ? "保存中..." : "保存宠物档案" }}
      </view>
    </view>
  </view>
</template>

<style scoped lang="scss">
.pet-form-page {
  min-height: 100vh;
  padding-bottom: 196rpx;
  background: linear-gradient(180deg, #fff8fa 0%, #f7fbff 100%);
}

.pet-form-page__scroll {
  height: 100vh;
}

.pet-form-page__shell {
  padding: 32rpx 24rpx 40rpx;
}

.pet-form-page__header {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
  margin-bottom: 24rpx;
}

.pet-form-page__topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.pet-form-page__back {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56rpx;
  height: 56rpx;
  border-radius: 50%;
  color: var(--text-primary);
  font-size: 42rpx;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: var(--shadow-card);
}

.pet-form-page__title {
  color: var(--text-primary);
  font-size: 44rpx;
  font-weight: 700;
  line-height: 1.3;
}

.pet-form-page__avatar-card {
  display: flex;
  align-items: center;
  gap: 24rpx;
}

.pet-form-page__avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  width: 148rpx;
  height: 148rpx;
  border-radius: 50%;
  overflow: hidden;
  color: #ca7c99;
  font-size: 58rpx;
  background: linear-gradient(180deg, rgba(255, 198, 211, 0.9) 0%, rgba(212, 240, 247, 0.95) 100%);
}

.pet-form-page__avatar image {
  width: 100%;
  height: 100%;
}

.pet-form-page__avatar-meta {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.pet-form-page__card-title {
  color: var(--text-primary);
  font-size: 32rpx;
  font-weight: 700;
}

.pet-form-page__upload-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 156rpx;
  min-height: 60rpx;
  padding: 0 20rpx;
  border-radius: 999rpx;
  color: #ffffff;
  font-size: var(--font-caption);
  background: linear-gradient(90deg, #b894dd 0%, #ff9fb6 100%);
}

.pet-form-page__section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20rpx;
}

.pet-form-page__required {
  color: var(--color-danger);
  font-size: var(--font-caption);
}

.pet-form-page__field {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
  margin-top: 20rpx;
}

.pet-form-page__field:first-of-type {
  margin-top: 0;
}

.pet-form-page__label {
  color: #d37898;
  font-size: var(--font-caption);
  font-weight: 600;
}

.pet-form-page__grid {
  display: flex;
  gap: 16rpx;
  flex-wrap: wrap;
}

.pet-form-page__field--half {
  flex: 1;
  min-width: 0;
}

.pet-form-page__picker {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.pet-form-page__picker--disabled {
  color: var(--text-placeholder);
}

.pet-form-page__arrow {
  color: var(--text-placeholder);
  font-size: 32rpx;
}

.pet-form-page__segmented {
  display: flex;
  gap: 14rpx;
}

.pet-form-page__segmented--three .pet-form-page__segmented-item {
  flex: 1;
}

.pet-form-page__segmented-item {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 84rpx;
  padding: 0 22rpx;
  border: 2rpx solid transparent;
  border-radius: 20rpx;
  color: var(--text-secondary);
  font-size: var(--font-body);
  background: #fff8fa;
}

.pet-form-page__segmented-item--active {
  color: #c8628a;
  border-color: rgba(255, 139, 167, 0.35);
  background: linear-gradient(180deg, rgba(255, 198, 211, 0.35) 0%, rgba(212, 240, 247, 0.3) 100%);
}

.pet-form-page__age-switch {
  display: flex;
  gap: 10rpx;
  padding: 8rpx;
  margin-top: 20rpx;
  background: #f5f0f5;
  border-radius: 999rpx;
}

.pet-form-page__age-tab {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 68rpx;
  border-radius: 999rpx;
  color: var(--text-secondary);
  font-size: var(--font-caption);
}

.pet-form-page__age-tab--active {
  color: var(--text-primary);
  font-weight: 600;
  background: #ffffff;
  box-shadow: 0 8rpx 16rpx rgba(216, 183, 194, 0.16);
}

.pet-form-page__footer {
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

.pet-form-page__footer-hint {
  color: var(--text-secondary);
  font-size: var(--font-mini);
  line-height: 1.5;
}
</style>
