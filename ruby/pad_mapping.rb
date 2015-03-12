com_files = Dir.glob("ylitalot-com/_posts/*markdown")
pad_files = {}

###
# find all PAD images
###
com_files.each do |fname|
  number = nil
  image = nil
  state = 0
  f = File.open(fname)
  f.each_line do |line|
    if state == 0 and line.start_with?("title: ")
      i2 = line.rindex("/")-1
      i1 = line.rindex("(",i2)+1
      number = line[i1..i2]
      state = 1
    elsif state == 1 and line.index("_c.jpg")
      i1 = line.index("/images/")
      i2 = line.index("_c.jpg",i1)-1
      image = line[i1..i2]
    end # if
  end # f.each_line
  if number.nil? or image.nil?
    puts("number or image nil on #{fname} (state == #{state})")
  else
    pad_files[image] = number.to_i
  end # if
  f.close()
end # com_files.each

###
# remove PAD images that have already been used
###
net_files = Dir.glob("ylitalot-net/_posts/*markdown")
net_files.each do |fname|
  f = File.open(fname)
  f.each_line do |line|
    if not line.index("/images/").nil?
      i1 = line.index("/images/")
      i2 = line.index(/(_c.jpg|_t.jpg|_l.jpg|\ |\))/,i1)
      image = line[i1..i2-1]
      # puts("+++ (#{line}) #{i1} #{i2}")
      # puts("+++ >#{image}<")
      if pad_files.key?(image)
        pad_files.delete(image)
      end # if
    end # if
  end # f.each_line
  f.close()
end # net_files.each

###
# transform Hash into list of missing PAD numbers
###
missing_pads = []
pad_files.each do |key,value|
  missing_pads += [value]
end # pad_files.each
puts("Missing PAD files: #{missing_pads.length}")

###
# truncate number list with integer ranges
###
missing_pads.sort()
last = prev = -1
trunc_list = ""
missing_pads.each do |cur|
  if (prev+1) == cur
    prev = cur
  elsif last < prev
    trunc_list += "-#{prev}, #{cur}"
    prev = last = cur
  else
    trunc_list += ", #{cur}"
    prev = last = cur
  end # if
  # puts "### #{cur} #{last} #{prev}"
end # missing_pads.each
if last < prev
  # puts "### add missing item #{prev} to list"
  trunc_list += "-#{prev}"
end # if
puts trunc_list[1..-1]
