/** Product image with a placeholder fallback.
 *
 *  `variant.image_url` can legitimately be empty — it isn't in the spec's
 *  original model and not every feed row carries one. Rendering
 *  <img src=""> would make the browser re-request the current page as the
 *  image, so an empty value has to become a real placeholder element.
 */
export default function ProductImage({ src, alt, className = "", loading = "lazy" }) {
  if (!src) {
    return (
      <div className={`${className} image-placeholder`.trim()} role="img" aria-label={`${alt} (kein Bild)`}>
        <span aria-hidden="true">kein Bild</span>
      </div>
    );
  }
  return <img className={className} src={src} alt={alt} loading={loading} />;
}
