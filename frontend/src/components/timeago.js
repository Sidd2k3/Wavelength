import { formatDistanceToNowStrict, format } from "date-fns";

export function timeAgo(value) {
  if (!value) return "";
  try {
    return formatDistanceToNowStrict(new Date(value), { addSuffix: true });
  } catch {
    return "";
  }
}

export function fullDate(value) {
  if (!value) return "";
  try {
    return format(new Date(value), "d MMM yyyy, h:mm a");
  } catch {
    return "";
  }
}
