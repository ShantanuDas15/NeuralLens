import useAuthedImage from '../../hooks/useAuthedImage';

/** <img> for protected backend images; accepts the same props as <img>. */
const AuthedImage = ({ src: url, alt, ...props }) => {
  const objectUrl = useAuthedImage(url);

  if (!objectUrl) return null;
  return <img src={objectUrl} alt={alt} {...props} />;
};

export default AuthedImage;
