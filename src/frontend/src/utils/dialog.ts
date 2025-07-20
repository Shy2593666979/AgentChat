import { ElMessageBox } from 'element-plus'

/**
 * 显示删除确认对话框（居中显示）
 * @param message 确认消息
 * @param title 对话框标题，默认为"删除确认"
 */
export const showDeleteConfirm = (message: string, title: string = '删除确认') => {
  return ElMessageBox.confirm(
    message,
    title,
    {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
      center: true,
      lockScroll: true,
      customClass: 'delete-confirm-dialog',
      dangerouslyUseHTMLString: false,
      distinguishCancelAndClose: true,
      showClose: true,
      closeOnClickModal: false,
      closeOnPressEscape: true
    }
  )
}

/**
 * 显示通用确认对话框（居中显示）
 * @param message 确认消息
 * @param title 对话框标题
 * @param options 额外选项
 */
export const showConfirm = (
  message: string, 
  title: string = '确认', 
  options: any = {}
) => {
  return ElMessageBox.confirm(
    message,
    title,
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
      center: true,
      lockScroll: true,
      customClass: 'center-dialog',
      ...options
    }
  )
} 