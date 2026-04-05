import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { CallToolResultSchema, ListToolsResultSchema } from "@modelcontextprotocol/sdk/types.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

class McpManager {
  constructor() {
    this.client = null;
    this.transport = null;
    this.ready = false;
    this.initializing = null;
    this.availableTools = [];
  }

  resolveMcpEntry() {
    const candidateFromEnv = process.env.BILIBILI_MCP_ENTRY;
    const fallback = path.resolve(__dirname, "../../../bilibili-mcp-js-main/dist/index.js");
    const entry = candidateFromEnv ? path.resolve(candidateFromEnv) : fallback;

    if (!fs.existsSync(entry)) {
      throw new Error(
        `未找到 bilibili MCP dist 入口：${entry}。请先在 bilibili-mcp-js-main 目录执行 npm install && npm run build，或配置 BILIBILI_MCP_ENTRY。`
      );
    }
    return entry;
  }

  async init() {
    if (this.ready && this.client) return;
    if (this.initializing) return this.initializing;

    this.initializing = (async () => {
      const mcpEntry = this.resolveMcpEntry();
      this.transport = new StdioClientTransport({
        command: "node",
        args: [mcpEntry],
      });

      this.client = new Client(
        {
          name: "pagelm-bilibili-mcp-client",
          version: "1.0.0",
        },
        {
          capabilities: {},
        }
      );

      await this.client.connect(this.transport);
      const tools = await this.client.request({ method: "tools/list" }, ListToolsResultSchema);
      this.availableTools = (tools.tools || []).map((tool) => tool.name);
      this.ready = true;
    })();

    try {
      await this.initializing;
    } finally {
      this.initializing = null;
    }
  }

  async close() {
    this.ready = false;
    this.availableTools = [];
    if (this.client) {
      await this.client.close();
      this.client = null;
    }
    this.transport = null;
  }

  parseMcpResult(result) {
    const textItem = (result.content || []).find((item) => item.type === "text");
    if (!textItem?.text) return [];
    try {
      const parsed = JSON.parse(textItem.text);
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return [];
    }
  }

  normalizeVideo(raw) {
    const title = (raw?.title || "").replace(/<[^>]+>/g, "").trim();
    const cover = raw?.pic || "";
    const bvid = raw?.bvid || "";
    const author = raw?.author || raw?.owner?.name || "";
    const duration = raw?.duration || "";
    const description = raw?.description || raw?.desc || "";

    return {
      title,
      cover,
      bvid,
      author,
      duration,
      description,
    };
  }

  async callSearchTool(keyword) {
    if (!this.client) throw new Error("MCP 客户端未初始化");

    const preferredTools = ["search_videos", "bilibili-search-summary"];
    const toolName = preferredTools.find((name) => this.availableTools.includes(name));

    if (!toolName) {
      throw new Error(`未找到可用搜索工具。当前可用工具：${this.availableTools.join(", ") || "无"}`);
    }

    const result = await this.client.request(
      {
        method: "tools/call",
        params: {
          name: toolName,
          arguments: { keyword },
        },
      },
      CallToolResultSchema
    );

    return this.parseMcpResult(result).map((item) => this.normalizeVideo(item));
  }

  async searchVideos(keyword) {
    const q = String(keyword || "").trim();
    if (!q) return [];
    if (!this.ready) {
      await this.init();
    }
    return this.callSearchTool(q);
  }
}

const mcpManager = new McpManager();
export default mcpManager;
