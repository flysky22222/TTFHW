#!/usr/bin/env bash
# env_check.sh — T-03: 检查并（可选）安装 TTFHW 测试所需的构建环境
#
# 用法:
#   ./env_check.sh                        # 检查通用 RPM 打包环境
#   ./env_check.sh openeuler              # 检查 openEuler 特有工具
#   ./env_check.sh fedora                 # 检查 Fedora 特有工具
#   ./env_check.sh fedora --install       # 检查并自动安装缺失工具
#   ./env_check.sh --list-communities     # 列出支持的社区
#
# 退出码:
#   0 = 所有必需工具已就绪
#   1 = 有工具缺失（未使用 --install）
#   2 = 安装失败

set -euo pipefail

# ── 颜色 ──────────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

ok()   { echo -e "  ${GREEN}✅ $*${RESET}"; }
fail() { echo -e "  ${RED}❌ $*${RESET}"; }
warn() { echo -e "  ${YELLOW}⚠️  $*${RESET}"; }
info() { echo -e "  ${CYAN}ℹ️  $*${RESET}"; }

# ── 参数解析 ─────────────────────────────────────────────────────────────────
COMMUNITY="${1:-}"
INSTALL=false
for arg in "$@"; do
  [[ "$arg" == "--install" ]] && INSTALL=true
  [[ "$arg" == "--list-communities" ]] && { echo "支持的社区: openeuler fedora"; exit 0; }
done

# ── 检测包管理器 ──────────────────────────────────────────────────────────────
detect_pkg_manager() {
  if command -v dnf &>/dev/null; then echo "dnf"
  elif command -v yum &>/dev/null; then echo "yum"
  elif command -v apt-get &>/dev/null; then echo "apt"
  else echo "unknown"; fi
}
PKG_MGR=$(detect_pkg_manager)

install_pkg() {
  local pkg="$1"
  if [[ "$INSTALL" != "true" ]]; then
    fail "$pkg 未安装（使用 --install 自动安装）"
    return 1
  fi
  echo -e "  ${CYAN}→ 安装 $pkg...${RESET}"
  case "$PKG_MGR" in
    dnf) sudo dnf install -y "$pkg" ;;
    yum) sudo yum install -y "$pkg" ;;
    apt) sudo apt-get install -y "$pkg" ;;
    *)   fail "无法识别包管理器，请手动安装: $pkg"; return 1 ;;
  esac
  ok "$pkg 已安装"
}

check_cmd() {
  local cmd="$1" pkg="${2:-$1}" desc="${3:-}"
  if command -v "$cmd" &>/dev/null; then
    local ver
    ver=$("$cmd" --version 2>/dev/null | head -1 || echo "已安装")
    ok "$cmd${desc:+  [$desc]}  →  $ver"
    return 0
  else
    install_pkg "$pkg" || return 1
  fi
}

# ── 通用 RPM 构建工具 ─────────────────────────────────────────────────────────
check_common() {
  echo -e "\n${BOLD}[ 通用 RPM 打包工具 ]${RESET}"
  local missing=0
  check_cmd rpmbuild    rpm-build      "构建 RPM"            || ((missing++))
  check_cmd rpmdev-setuptree rpmdevtools "初始化工作目录"    || ((missing++))
  check_cmd spectool    rpmdevtools    "下载 Source 文件"    || ((missing++))
  check_cmd rpmlint     rpmlint        "spec lint 检查"      || ((missing++))
  check_cmd git         git            "版本控制"            || ((missing++))

  echo -e "\n${BOLD}[ rpmbuild 工作目录 ]${RESET}"
  local rpmbuild_dir="$HOME/rpmbuild"
  if [[ -d "$rpmbuild_dir/SPECS" ]]; then
    ok "~/rpmbuild 工作目录已存在"
  else
    warn "~/rpmbuild 未初始化，运行: rpmdev-setuptree"
    if [[ "$INSTALL" == "true" ]] && command -v rpmdev-setuptree &>/dev/null; then
      rpmdev-setuptree
      ok "已运行 rpmdev-setuptree"
    fi
  fi
  return $missing
}

# ── openEuler 特有检查 ────────────────────────────────────────────────────────
check_openeuler() {
  echo -e "\n${BOLD}[ openEuler 特有工具 ]${RESET}"
  local missing=0

  check_cmd osc osc "OBS Service Client (OBS 构建客户端)" || ((missing++))

  # 检查 OBS 配置
  if [[ -f "$HOME/.oscrc" ]]; then
    ok "~/.oscrc 已配置"
  else
    warn "~/.oscrc 未配置，需要运行: osc config https://build.openeuler.org"
    info "文档: https://docs.openeuler.org/en/docs/24.03_LTS/docs/ApplicationDev/building-an-rpm-package.html"
  fi

  # 检查 Gitee SSH key
  echo -e "\n${BOLD}[ Gitee/AtomGit 访问 ]${RESET}"
  if ssh -T git@gitee.com 2>&1 | grep -q "successfully authenticated"; then
    ok "Gitee SSH 认证正常"
  else
    warn "Gitee SSH 未配置或认证失败"
    info "需要在 https://gitee.com/profile/sshkeys 上传公钥"
  fi

  echo -e "\n${BOLD}[ CLA 状态 ]${RESET}"
  info "请确认已在以下地址签署 openEuler CLA："
  info "https://clasign.osinfra.cn/sign/gitee_openeuler-1611298811283968340"

  return $missing
}

# ── Fedora 特有检查 ───────────────────────────────────────────────────────────
check_fedora() {
  echo -e "\n${BOLD}[ Fedora 特有工具 ]${RESET}"
  local missing=0

  check_cmd mock       mock    "chroot 隔离构建"  || ((missing++))
  check_cmd fedpkg     fedpkg  "Fedora 包管理工具" || ((missing++))
  check_cmd koji       koji    "Koji 构建系统客户端" || ((missing++))

  # 检查 mock 组
  echo -e "\n${BOLD}[ mock 组权限 ]${RESET}"
  if id -nG "$USER" | grep -qw mock; then
    ok "用户 $USER 已在 mock 组中"
  else
    fail "用户 $USER 不在 mock 组"
    if [[ "$INSTALL" == "true" ]]; then
      sudo usermod -a -G mock "$USER"
      warn "已添加到 mock 组，需要重新登录后生效"
    else
      info "修复: sudo usermod -a -G mock \$USER  （然后重新登录）"
      ((missing++))
    fi
  fi

  # 检查 FAS 配置
  echo -e "\n${BOLD}[ Fedora 账号配置 ]${RESET}"
  if [[ -f "$HOME/.fedora.upn" ]]; then
    local upn
    upn=$(cat "$HOME/.fedora.upn")
    ok "FAS 用户名: $upn"
  else
    warn "~/.fedora.upn 未配置（运行 fedpkg 时会提示）"
  fi

  if fedpkg whoami &>/dev/null 2>&1; then
    ok "fedpkg 认证正常"
  else
    warn "fedpkg 认证未配置或失败"
    info "文档: https://docs.fedoraproject.org/en-US/package-maintainers/Joining_the_Package_Maintainers/"
  fi

  echo -e "\n${BOLD}[ Sponsorship 状态 ]${RESET}"
  info "请确认已获得 Fedora packager 组 Sponsorship："
  info "https://docs.fedoraproject.org/en-US/package-maintainers/How_to_Get_Sponsored_into_the_Packager_Group/"

  return $missing
}

# ── 主流程 ────────────────────────────────────────────────────────────────────
echo -e "${BOLD}TTFHW 环境检查工具${RESET}"
echo -e "社区: ${CYAN}${COMMUNITY:-通用}${RESET}  |  自动安装: ${INSTALL}"
echo "────────────────────────────────────────────────────────────"

TOTAL_MISSING=0

check_common || TOTAL_MISSING=$((TOTAL_MISSING + $?))

case "${COMMUNITY,,}" in
  openeuler|openeuler*)
    check_openeuler || TOTAL_MISSING=$((TOTAL_MISSING + $?)) ;;
  fedora)
    check_fedora || TOTAL_MISSING=$((TOTAL_MISSING + $?)) ;;
  "")
    info "提示: 传入社区名可检查特定工具 (openeuler / fedora)" ;;
  *)
    warn "未知社区: $COMMUNITY（仅检查通用工具）" ;;
esac

# ── 汇总 ──────────────────────────────────────────────────────────────────────
echo ""
echo "════════════════════════════════════════════════════════════"
if [[ $TOTAL_MISSING -eq 0 ]]; then
  echo -e "${GREEN}${BOLD}✅ 环境检查通过，可以开始 TTFHW 测试！${RESET}"
  exit 0
else
  echo -e "${RED}${BOLD}❌ 有 $TOTAL_MISSING 个工具缺失。${RESET}"
  echo -e "   运行 ${CYAN}$0 ${COMMUNITY:-} --install${RESET} 自动安装"
  exit 1
fi
