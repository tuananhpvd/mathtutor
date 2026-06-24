export function saveSession(token, vai_tro, ho_ten) {
  sessionStorage.setItem('token', token)
  sessionStorage.setItem('vai_tro', vai_tro)
  sessionStorage.setItem('ho_ten', ho_ten)
}

export function clearSession() {
  sessionStorage.removeItem('token')
  sessionStorage.removeItem('vai_tro')
  sessionStorage.removeItem('ho_ten')
}

export function getSession() {
  const token = sessionStorage.getItem('token')
  if (!token) return null
  return {
    token,
    vai_tro: sessionStorage.getItem('vai_tro'),
    ho_ten: sessionStorage.getItem('ho_ten'),
  }
}
