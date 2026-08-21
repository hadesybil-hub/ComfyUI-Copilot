// Copyright (C) 2025 AIDC-AI
// Licensed under the MIT License.

const isDevelopment = import.meta.env.MODE === 'development'

// Production requests must stay on the current ComfyUI origin. An external
// service can still be supplied explicitly for development builds.
const defaultApiBaseUrl = ''

export const github_url = 'https://github.com/AIDC-AI/ComfyUI-Copilot'

export const config = {
  apiBaseUrl: isDevelopment 
    ? (import.meta.env.VITE_API_BASE_URL || defaultApiBaseUrl)
    : (import.meta.env.VITE_API_BASE_URL || defaultApiBaseUrl)
}
