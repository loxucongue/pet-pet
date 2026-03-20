/** AI 对话流式请求工具。 */
import { buildApiUrl, getAuthHeaders } from "@/utils/request.js";

const STREAM_TIMEOUT = 90000;
const POLL_INTERVAL = 500;

function createParser(onEvent) {
  let buffer = "";

  function emit(rawBlock) {
    if (!rawBlock.trim()) {
      return;
    }

    let eventName = "message";
    const dataLines = [];

    rawBlock.split("\n").forEach((line) => {
      if (line.startsWith("event:")) {
        eventName = line.slice(6).trim() || "message";
      } else if (line.startsWith("data:")) {
        dataLines.push(line.slice(5).trimStart());
      }
    });

    onEvent({
      event: eventName,
      data: dataLines.join("\n"),
    });
  }

  return {
    feed(chunk) {
      if (!chunk) {
        return;
      }

      buffer += String(chunk).replace(/\r\n/g, "\n");

      let separatorIndex = buffer.indexOf("\n\n");
      while (separatorIndex >= 0) {
        emit(buffer.slice(0, separatorIndex));
        buffer = buffer.slice(separatorIndex + 2);
        separatorIndex = buffer.indexOf("\n\n");
      }
    },
    flush() {
      emit(buffer);
      buffer = "";
    },
  };
}

function parseJsonSafely(value) {
  if (!value) {
    return null;
  }

  try {
    return JSON.parse(value);
  } catch (error) {
    return null;
  }
}

function buildStreamError(payload, fallbackMessage) {
  if (!payload) {
    return new Error(fallbackMessage);
  }

  if (typeof payload === "string") {
    const parsed = parseJsonSafely(payload);
    if (parsed) {
      return buildStreamError(parsed, fallbackMessage);
    }
    return new Error(payload || fallbackMessage);
  }

  const detail = payload.detail || payload.message || fallbackMessage;
  const error = new Error(detail);
  if (payload.remaining !== undefined) {
    error.remaining = payload.remaining;
  }
  if (payload.statusCode !== undefined) {
    error.statusCode = payload.statusCode;
  }
  return error;
}

async function readResponseBodyText(response) {
  try {
    return await response.text();
  } catch (error) {
    return "";
  }
}

function parseSseText(rawText) {
  const events = [];
  const parser = createParser((eventPayload) => {
    events.push(eventPayload);
  });
  parser.feed(`${rawText || ""}\n\n`);
  parser.flush();
  return events;
}

function resolveAssistantMessage(messages = [], knownMessageCount = 0) {
  const sortedMessages = Array.isArray(messages) ? messages.slice() : [];
  const latestAssistant = sortedMessages
    .slice()
    .reverse()
    .find((item) => item.role === "assistant");

  if (!latestAssistant) {
    return null;
  }

  if (sortedMessages.length < knownMessageCount + 2) {
    return null;
  }

  return latestAssistant;
}

function normalizeResponseError(statusCode, responseBodyText) {
  const parsedBody = parseJsonSafely(responseBodyText);
  if (parsedBody && typeof parsedBody === "object") {
    return buildStreamError(
      {
        ...parsedBody,
        statusCode,
      },
      "AI 对话暂时不可用，请稍后重试。",
    );
  }

  return buildStreamError(
    {
      detail: responseBodyText || `请求失败（${statusCode}）`,
      statusCode,
    },
    "AI 对话暂时不可用，请稍后重试。",
  );
}

function createFetchStreamTask(options) {
  const {
    url,
    body,
    onStart,
    onMessage,
    onDone,
    onError,
  } = options;

  const controller = typeof AbortController !== "undefined" ? new AbortController() : null;
  let finished = false;
  let cancelled = false;

  const promise = (async () => {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        ...getAuthHeaders(
          {
            Accept: "text/event-stream",
          },
          true,
        ),
      },
      body: JSON.stringify(body),
      signal: controller?.signal,
    });

    if (!response.ok) {
      const responseText = await readResponseBodyText(response);
      throw normalizeResponseError(response.status, responseText);
    }

    const reader = response.body?.getReader?.();
    if (!reader) {
      throw new Error("当前环境不支持流式读取。");
    }

    const decoder = typeof TextDecoder !== "undefined" ? new TextDecoder("utf-8") : null;
    const parser = createParser((eventPayload) => {
      if (finished) {
        return;
      }

      if (eventPayload.event === "start") {
        onStart(parseJsonSafely(eventPayload.data) || {});
        return;
      }

      if (eventPayload.event === "message") {
        onMessage(eventPayload.data || "");
        return;
      }

      if (eventPayload.event === "done") {
        finished = true;
        onDone(parseJsonSafely(eventPayload.data) || {});
        return;
      }

      if (eventPayload.event === "error") {
        finished = true;
        throw buildStreamError(eventPayload.data, "AI 对话暂时不可用，请稍后重试。");
      }
    });

    while (!finished) {
      const { done, value } = await reader.read();
      if (done) {
        parser.flush();
        if (!finished) {
          finished = true;
          onDone({});
        }
        break;
      }

      const chunk = decoder ? decoder.decode(value, { stream: true }) : "";
      parser.feed(chunk);
    }
  })()
    .catch((error) => {
      if (cancelled) {
        return;
      }
      onError(buildStreamError(error, "AI 对话暂时不可用，请稍后重试。"));
      throw error;
    });

  return {
    promise,
    cancel() {
      cancelled = true;
      controller?.abort?.();
    },
  };
}

function createAppPlusStreamTask(options) {
  const {
    url,
    body,
    onStart,
    onMessage,
    onDone,
    onError,
  } = options;

  let xhr = null;
  let finished = false;
  let cancelled = false;

  const promise = new Promise((resolve, reject) => {
    try {
      xhr = new plus.net.XMLHttpRequest();
      const parser = createParser((eventPayload) => {
        if (finished) {
          return;
        }

        if (eventPayload.event === "start") {
          onStart(parseJsonSafely(eventPayload.data) || {});
          return;
        }

        if (eventPayload.event === "message") {
          onMessage(eventPayload.data || "");
          return;
        }

        if (eventPayload.event === "done") {
          finished = true;
          onDone(parseJsonSafely(eventPayload.data) || {});
          resolve();
          return;
        }

        if (eventPayload.event === "error") {
          finished = true;
          const error = buildStreamError(eventPayload.data, "AI 对话暂时不可用，请稍后重试。");
          onError(error);
          reject(error);
        }
      });

      let consumedLength = 0;
      xhr.onreadystatechange = () => {
        if (!xhr) {
          return;
        }

        if (xhr.readyState === 3 || xhr.readyState === 4) {
          const nextText = xhr.responseText.slice(consumedLength);
          consumedLength = xhr.responseText.length;
          parser.feed(nextText);
        }

        if (xhr.readyState === 4 && !finished) {
          parser.flush();
          if (xhr.status < 200 || xhr.status >= 300) {
            const error = normalizeResponseError(xhr.status, xhr.responseText);
            if (!cancelled) {
              onError(error);
            }
            reject(error);
            return;
          }

          finished = true;
          onDone({});
          resolve();
        }
      };

      xhr.onerror = () => {
        const error = new Error("网络异常，请检查网络连接。");
        if (!cancelled) {
          onError(error);
        }
        reject(error);
      };

      xhr.ontimeout = () => {
        const error = new Error("AI 对话超时，请稍后重试。");
        if (!cancelled) {
          onError(error);
        }
        reject(error);
      };

      xhr.timeout = STREAM_TIMEOUT;
      xhr.open("POST", url, true);
      const headers = getAuthHeaders(
        {
          Accept: "text/event-stream",
        },
        true,
      );
      Object.keys(headers).forEach((headerName) => {
        xhr.setRequestHeader(headerName, headers[headerName]);
      });
      xhr.send(JSON.stringify(body));
    } catch (error) {
      const normalizedError = buildStreamError(error, "AI 对话暂时不可用，请稍后重试。");
      if (!cancelled) {
        onError(normalizedError);
      }
      reject(normalizedError);
    }
  });

  return {
    promise,
    cancel() {
      cancelled = true;
      if (xhr) {
        xhr.abort();
      }
    },
  };
}

function createPollingFallbackTask(options) {
  const {
    url,
    body,
    knownMessageCount,
    onStart,
    onMessage,
    onDone,
    onError,
    pollMessages,
    fetchQuota,
  } = options;

  let cancelled = false;
  let settled = false;
  let requestFinished = false;
  let responseStatusCode = 0;
  let responseText = "";

  const promise = new Promise((resolve, reject) => {
    onStart({
      session_id: body.session_id || null,
    });

    uni.request({
      url,
      method: "POST",
      timeout: STREAM_TIMEOUT,
      header: getAuthHeaders(
        {
          Accept: "text/event-stream",
        },
        true,
      ),
      data: body,
      success: (response) => {
        responseStatusCode = response.statusCode;
        responseText = typeof response.data === "string" ? response.data : "";
        requestFinished = true;
      },
      fail: (error) => {
        requestFinished = true;
        if (!settled) {
          const normalizedError = buildStreamError(error, "网络异常，请检查网络连接。");
          settled = true;
          onError(normalizedError);
          reject(normalizedError);
        }
      },
    });

    const poll = async () => {
      if (cancelled || settled) {
        return;
      }

      try {
        if (typeof pollMessages === "function") {
          const messagePayload = await pollMessages();
          const latestAssistant = resolveAssistantMessage(messagePayload?.items, knownMessageCount);
          if (latestAssistant?.content) {
            settled = true;
            onMessage(latestAssistant.content, true);
            const quotaPayload = typeof fetchQuota === "function" ? await fetchQuota() : {};
            onDone({
              remaining: quotaPayload?.remaining ?? null,
              assistant_message_id: latestAssistant.id,
            });
            resolve();
            return;
          }
        }

        if (requestFinished) {
          if (responseStatusCode && (responseStatusCode < 200 || responseStatusCode >= 300)) {
            const error = normalizeResponseError(responseStatusCode, responseText);
            settled = true;
            onError(error);
            reject(error);
            return;
          }

          const events = parseSseText(responseText);
          const errorEvent = events.find((item) => item.event === "error");
          if (errorEvent) {
            const error = buildStreamError(errorEvent.data, "AI 对话暂时不可用，请稍后重试。");
            settled = true;
            onError(error);
            reject(error);
            return;
          }

          const messageText = events
            .filter((item) => item.event === "message")
            .map((item) => item.data || "")
            .join("");
          const doneEvent = events.find((item) => item.event === "done");

          if (messageText) {
            settled = true;
            onMessage(messageText, true);
            onDone(parseJsonSafely(doneEvent?.data) || {});
            resolve();
            return;
          }
        }
      } catch (error) {
        if (!settled) {
          const normalizedError = buildStreamError(error, "AI 对话暂时不可用，请稍后重试。");
          settled = true;
          onError(normalizedError);
          reject(normalizedError);
          return;
        }
      }

      setTimeout(poll, POLL_INTERVAL);
    };

    poll();
  });

  return {
    promise,
    cancel() {
      cancelled = true;
    },
  };
}

export function createChatStreamTask(options) {
  const {
    sessionId,
    content,
    knownMessageCount = 0,
    pollMessages,
    fetchQuota,
    onStart = () => {},
    onMessage = () => {},
    onDone = () => {},
    onError = () => {},
  } = options;

  const url = buildApiUrl(`/api/chat/sessions/${sessionId}/send`);
  const body = {
    content,
    session_id: sessionId,
  };

  if (typeof fetch === "function" && typeof window !== "undefined") {
    return createFetchStreamTask({
      url,
      body,
      onStart,
      onMessage,
      onDone,
      onError,
    });
  }

  if (typeof plus !== "undefined" && plus?.net?.XMLHttpRequest) {
    return createAppPlusStreamTask({
      url,
      body,
      onStart,
      onMessage,
      onDone,
      onError,
    });
  }

  return createPollingFallbackTask({
    url,
    body,
    knownMessageCount,
    pollMessages,
    fetchQuota,
    onStart,
    onMessage,
    onDone,
    onError,
  });
}
