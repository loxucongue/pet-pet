/** AI 对话模块接口。 */
import { del, get, post } from "@/utils/request.js";
import { createChatStreamTask } from "@/utils/chat-stream.js";

function withLongTimeout(options = {}) {
  return {
    timeout: 90000,
    ...options,
  };
}

export function createChatSession(data, options) {
  return post("/api/chat/sessions", data, options);
}

export function getChatSessions(params, options) {
  return get("/api/chat/sessions", params, options);
}

export function getChatSessionMessages(sessionId, params, options) {
  return get(`/api/chat/sessions/${sessionId}/messages`, params, options);
}

export function deleteChatSession(sessionId, options) {
  return del(`/api/chat/sessions/${sessionId}`, undefined, options);
}

export function getChatQuota(options) {
  return get("/api/chat/quota", undefined, options);
}

export function getChatPermissions(options) {
  return get("/api/chat/permissions", undefined, options);
}

export function streamChatMessage(sessionId, content, handlers = {}, options = {}) {
  const knownMessageCount = Number(options.knownMessageCount || 0);

  return createChatStreamTask({
    sessionId,
    content,
    knownMessageCount,
    onStart: handlers.onStart,
    onMessage: handlers.onMessage,
    onDone: handlers.onDone,
    onError: handlers.onError,
    pollMessages: () =>
      getChatSessionMessages(
        sessionId,
        {
          page: 1,
          page_size: 100,
        },
        {
          showLoading: false,
          timeout: 5000,
        },
      ),
    fetchQuota: () => getChatQuota({ showLoading: false }),
    ...withLongTimeout(options),
  });
}
