/**
 * 文字列を最大長で切り詰める。超過した場合は末尾に「…」を付ける。
 */
export function truncate(value: string, maxLength: number): string {
  if (value.length <= maxLength) {
    return value;
  }
  return `${value.slice(0, maxLength)}…`;
}
