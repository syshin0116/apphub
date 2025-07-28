# Next.js 웹 앱용 Dockerfile
FROM node:18-alpine AS base

# 의존성 설치 단계
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

# 루트 package.json과 pnpm-lock.yaml 복사
COPY ../../package.json ../../pnpm-lock.yaml ./
COPY ../../pnpm-workspace.yaml ./

# 웹 앱 package.json 복사
COPY package.json ./apps/web/

# 의존성 설치
RUN npm install -g pnpm
RUN pnpm install --frozen-lockfile

# 빌드 단계
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# 환경 변수 설정
ENV NEXT_TELEMETRY_DISABLED 1

# 빌드 실행
RUN npm install -g pnpm
RUN pnpm build

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