export function saveSession(token, vai_tro, ho_ten, la_quan_ly = false) {
  sessionStorage.setItem('token', token)
  sessionStorage.setItem('vai_tro', vai_tro)
  sessionStorage.setItem('ho_ten', ho_ten)
  sessionStorage.setItem('la_quan_ly', la_quan_ly ? '1' : '')
}

export function updateHoTen(ho_ten) {
  sessionStorage.setItem('ho_ten', ho_ten)
}

export function clearSession() {
  sessionStorage.removeItem('token')
  sessionStorage.removeItem('vai_tro')
  sessionStorage.removeItem('ho_ten')
  sessionStorage.removeItem('la_quan_ly')
}

export function getSession() {
  const token = sessionStorage.getItem('token')
  if (!token) return null
  return {
    token,
    vai_tro: sessionStorage.getItem('vai_tro'),
    ho_ten: sessionStorage.getItem('ho_ten'),
    la_quan_ly: sessionStorage.getItem('la_quan_ly') === '1',
  }
}
