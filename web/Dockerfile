# Next.js frontend. Built separately from the Flask API image — they are two
# deployables that happen to live in one repository.

FROM node:24-alpine AS deps
WORKDIR /app
# Dependencies in their own layer: package.json changes far less often than
# source, so editing a component does not reinstall node_modules.
COPY package.json package-lock.json ./
RUN npm ci


FROM node:24-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Baked in at build time by Next, so it must be present here and not only at
# runtime. Points at the Flask service on the compose network.
ARG FLASK_ORIGIN=http://api:8000
ENV FLASK_ORIGIN=$FLASK_ORIGIN
ENV NEXT_TELEMETRY_DISABLED=1

RUN npm run build


FROM node:24-alpine AS runtime
WORKDIR /app

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0

RUN addgroup -g 10001 -S nodejs && adduser -u 10001 -S nextjs -G nodejs

# `output: standalone` emits a self-contained server plus only the node_modules
# it actually uses. static/ and public/ are not included and must be copied.
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
COPY --from=builder --chown=nextjs:nodejs /app/public ./public

USER nextjs
EXPOSE 3000

CMD ["node", "server.js"]
