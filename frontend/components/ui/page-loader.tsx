import { Loader } from "./loader"

interface PageLoaderProps {
  text?: string
}

export function PageLoader({ text = "Loading..." }: PageLoaderProps) {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <Loader size="lg" text={text} />
    </div>
  )
}

