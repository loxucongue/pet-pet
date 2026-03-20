/** 宠物模块接口。 */
import { del, get, post, put } from "@/utils/request.js";

export function getPetList(params, options) {
  return get("/api/pets", params, options);
}

export function getPetDetail(petId, options) {
  return get(`/api/pets/${petId}`, undefined, options);
}

export function createPet(data, options) {
  return post("/api/pets", data, options);
}

export function updatePet(petId, data, options) {
  return put(`/api/pets/${petId}`, data, options);
}

export function deletePet(petId, options) {
  return del(`/api/pets/${petId}`, undefined, options);
}
