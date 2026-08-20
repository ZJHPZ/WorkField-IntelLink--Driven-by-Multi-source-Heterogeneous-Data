// 脸素材 — 文件名 → SVG 导入映射
// 用于从后端存储的文件名回显头像
import avatarAngry from '@/assets/icons/lian/angry-bored-disappointed-svgrepo-com.svg'
import avatarAngry2 from '@/assets/icons/lian/angry-bored-emoji-svgrepo-com.svg'
import avatarAnime from '@/assets/icons/lian/anime-emoji-emoticon-2-svgrepo-com.svg'
import avatarAnime2 from '@/assets/icons/lian/anime-emoji-emoticon-svgrepo-com.svg'
import avatarAwkward from '@/assets/icons/lian/awkward-drop-emoji-svgrepo-com.svg'
import avatarBlink from '@/assets/icons/lian/blink-emoji-emoticon-svgrepo-com.svg'
import avatarBored from '@/assets/icons/lian/bored-disappointed-emoji-svgrepo-com.svg'
import avatarCry from '@/assets/icons/lian/cry-emoji-emoticon-2-svgrepo-com.svg'
import avatarCry2 from '@/assets/icons/lian/cry-emoji-emoticon-svgrepo-com.svg'
import avatarCrying from '@/assets/icons/lian/crying-emoji-emoticon-svgrepo-com.svg'
import avatarDead from '@/assets/icons/lian/dead-emoji-emoticon-svgrepo-com.svg'
import avatarDisgusted from '@/assets/icons/lian/disgusted-emoji-emoticon-svgrepo-com.svg'
import avatarEmotion from '@/assets/icons/lian/emoji-emoticon-emotion-svgrepo-com.svg'
import avatarEyes from '@/assets/icons/lian/emoji-emoticon-eyes-svgrepo-com.svg'
import avatarFake from '@/assets/icons/lian/emoji-emoticon-fake-svgrepo-com.svg'
import avatarHappy from '@/assets/icons/lian/emoji-emoticon-happy-svgrepo-com.svg'
import avatarHappy2 from '@/assets/icons/lian/emoji-emoticon-happy-2-svgrepo-com.svg'
import avatarHappy3 from '@/assets/icons/lian/emoji-emoticon-happy-3-svgrepo-com.svg'
import avatarHappy4 from '@/assets/icons/lian/emoji-emoticon-happy-4-svgrepo-com.svg'
import avatarHeart from '@/assets/icons/lian/emoji-emoticon-heart-svgrepo-com.svg'
import avatarPain from '@/assets/icons/lian/emoji-emoticon-pain-svgrepo-com.svg'
import avatarSad from '@/assets/icons/lian/emoji-emoticon-sad-svgrepo-com.svg'
import avatarSad2 from '@/assets/icons/lian/emoji-emoticon-sad-2-svgrepo-com.svg'
import avatarSad3 from '@/assets/icons/lian/emoji-emoticon-sad-3-svgrepo-com.svg'
import avatarSad4 from '@/assets/icons/lian/emoji-emoticon-sad-4-svgrepo-com.svg'
import avatarSleep from '@/assets/icons/lian/emoji-emoticon-sleep-svgrepo-com.svg'

export const avatarList = [
  avatarHappy, avatarHappy2, avatarHappy3, avatarHappy4, avatarHeart,
  avatarAnime, avatarAnime2, avatarBlink, avatarEyes, avatarEmotion,
  avatarFake, avatarAwkward, avatarAngry, avatarAngry2, avatarBored,
  avatarCry, avatarCry2, avatarCrying, avatarSad, avatarSad2,
  avatarSad3, avatarSad4, avatarDisgusted, avatarPain, avatarDead, avatarSleep,
]

const avatarMap = new Map<string, string>([
  ['emoji-emoticon-happy-svgrepo-com', avatarHappy],
  ['emoji-emoticon-happy-2-svgrepo-com', avatarHappy2],
  ['emoji-emoticon-happy-3-svgrepo-com', avatarHappy3],
  ['emoji-emoticon-happy-4-svgrepo-com', avatarHappy4],
  ['emoji-emoticon-heart-svgrepo-com', avatarHeart],
  ['anime-emoji-emoticon-2-svgrepo-com', avatarAnime],
  ['anime-emoji-emoticon-svgrepo-com', avatarAnime2],
  ['blink-emoji-emoticon-svgrepo-com', avatarBlink],
  ['emoji-emoticon-eyes-svgrepo-com', avatarEyes],
  ['emoji-emoticon-emotion-svgrepo-com', avatarEmotion],
  ['emoji-emoticon-fake-svgrepo-com', avatarFake],
  ['awkward-drop-emoji-svgrepo-com', avatarAwkward],
  ['angry-bored-disappointed-svgrepo-com', avatarAngry],
  ['angry-bored-emoji-svgrepo-com', avatarAngry2],
  ['bored-disappointed-emoji-svgrepo-com', avatarBored],
  ['cry-emoji-emoticon-2-svgrepo-com', avatarCry],
  ['cry-emoji-emoticon-svgrepo-com', avatarCry2],
  ['crying-emoji-emoticon-svgrepo-com', avatarCrying],
  ['emoji-emoticon-sad-svgrepo-com', avatarSad],
  ['emoji-emoticon-sad-2-svgrepo-com', avatarSad2],
  ['emoji-emoticon-sad-3-svgrepo-com', avatarSad3],
  ['emoji-emoticon-sad-4-svgrepo-com', avatarSad4],
  ['disgusted-emoji-emoticon-svgrepo-com', avatarDisgusted],
  ['emoji-emoticon-pain-svgrepo-com', avatarPain],
  ['dead-emoji-emoticon-svgrepo-com', avatarDead],
  ['emoji-emoticon-sleep-svgrepo-com', avatarSleep],
])

export function getAvatarSrc(avatarUrl: string): string {
  if (!avatarUrl) return ''
  // 完整路径（本地即时设置或旧数据）
  if (avatarUrl.includes('/')) {
    // 尝试从路径中提取文件名再映射
    for (const [name, src] of avatarMap) {
      if (avatarUrl.includes(name)) return src
    }
    return avatarUrl
  }
  return avatarMap.get(avatarUrl) || ''
}

export function getAvatarFileName(avatarSrc: string): string {
  for (const [name, src] of avatarMap) {
    if (src === avatarSrc) return name
  }
  return ''
}
