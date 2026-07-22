import { get } from './client'

export interface ModelsInfo {
  providers: string[]
  current: {
    llm_provider: string
    llm_model: string
    llm_api_base: string
    embedding_provider: string
    embedding_model: string
  }
}

export function listModels() {
  return get<ModelsInfo>("/settings/models")
}