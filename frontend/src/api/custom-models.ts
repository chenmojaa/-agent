import { postJson, get } from './client'

export interface CustomModelsResponse {
  provider: string
  base_url: string
  models: string[]
}

export interface CustomModelsRequest {
  base_url: string
  api_key: string
}

export async function detectModels(req: CustomModelsRequest): Promise<CustomModelsResponse> {
  return postJson<CustomModelsResponse>('/settings/custom-models', req)
}

export { get }