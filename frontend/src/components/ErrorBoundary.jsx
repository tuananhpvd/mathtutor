import { Component } from 'react'
import Button from './ui/Button'
import ThuongHieu from './ThuongHieu'
import { clearSession } from '../auth'

export default class ErrorBoundary extends Component {
  state = { loi: null }

  static getDerivedStateFromError(loi) {
    return { loi }
  }

  componentDidCatch(loi, info) {
    console.error('Lỗi giao diện chưa xử lý:', loi, info)
  }

  render() {
    if (!this.state.loi) return this.props.children

    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-6 bg-bg px-6 text-center">
        <ThuongHieu size="md" onDark={false} />
        <div className="flex flex-col gap-2">
          <p className="text-lg font-semibold text-ink">Đã có lỗi xảy ra</p>
          <p className="max-w-md text-sm text-muted">
            Trang gặp sự cố ngoài dự kiến. Vui lòng tải lại trang; nếu vẫn còn lỗi, hãy đăng xuất
            rồi đăng nhập lại.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button onClick={() => window.location.reload()}>Tải lại trang</Button>
          <Button
            variant="secondary"
            onClick={() => {
              clearSession()
              window.location.reload()
            }}
          >
            Đăng xuất & tải lại
          </Button>
        </div>
      </div>
    )
  }
}
