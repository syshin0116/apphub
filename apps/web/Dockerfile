# Next.js 웹 앱용 Dockerfile (dev + prod)
FROM node:20-alpine AS base

# 의존성 설치 단계
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

  # 루트 및 워크스페이스 메타 복사 (모노레포 설치 준비)
  COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
  COPY apps/web/package.json apps/web/package.json
  COPY packages/ui/package.json packages/ui/package.json
  COPY packages/eslint-config/package.json packages/eslint-config/package.json
  COPY packages/typescript-config/package.json packages/typescript-config/package.json

# 의존성 설치
  RUN npm install -g pnpm && pnpm install --frozen-lockfile

# 빌드 단계
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
  COPY . .

# 환경 변수 설정
ENV NEXT_TELEMETRY_DISABLED 1

# 빌드 실행
  RUN npm install -g pnpm && pnpm build

# 개발용 런타임 (HMR)
FROM base AS dev
  WORKDIR /app
  ENV NODE_ENV development
  RUN npm install -g pnpm
  COPY --from=deps /app/node_modules ./node_modules
  COPY . .
  EXPOSE 3000
  ENV HOSTNAME 0.0.0.0
  CMD ["pnpm", "--filter", "web", "dev", "--port", "3000", "--hostname", "0.0.0.0"]

# 프로덕션 단계
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# 빌드된 앱 복사
  COPY --from=builder /app/apps/web/public ./apps/web/public

# 자동으로 생성된 standalone 출력 사용
COPY --from=builder --chown=nextjs:nodejs /app/apps/web/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/apps/web/.next/static ./apps/web/.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

  CMD ["node", "apps/web/server.js"]