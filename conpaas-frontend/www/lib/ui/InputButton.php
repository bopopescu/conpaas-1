<?php
/*
 * Copyright (c) 2010-2012, Contrail consortium.
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms,
 * with or without modification, are permitted provided
 * that the following conditions are met:
 *
 *  1. Redistributions of source code must retain the
 *     above copyright notice, this list of conditions
 *     and the following disclaimer.
 *  2. Redistributions in binary form must reproduce
 *     the above copyright notice, this list of
 *     conditions and the following disclaimer in the
 *     documentation and/or other materials provided
 *     with the distribution.
 *  3. Neither the name of the Contrail consortium nor the
 *     names of its contributors may be used to endorse
 *     or promote products derived from this software
 *     without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND
 * CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
 * INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
 * MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
 * CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 * SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
 * BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
 * WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
 * OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 */

function InputButton($text) {
	return new InputButton($text);
}

class InputButton {

	protected $id = '';
	protected $text;
	protected $visible = true;
	protected $disabled = false;
	protected $title = '';

	public function __construct($text) {
		$this->text = $text;
	}

	public function setVisible($visible) {
		$this->visible = $visible;
		return $this;
	}

	public function setId($id) {
		$this->id = $id;
		return $this;
	}

	public function setDisabled($disabled) {
		$this->disabled = $disabled;
		return $this;
	}

	public function setTitle($title) {
		$this->title = $title;
		return $this;
	}

	private function invisibleClass() {
		if ($this->visible) {
			return '';
		}
		return 'invisible';
	}

	private function disabledMarker() {
		if ($this->disabled) {
			return ' disabled="disabled" ';
		}
		return '';
	}

	public function __toString() {
		return
			'<input id="'.$this->id.'" type="button" '
			.' title="'.$this->title.'"'
			.' class="button '.$this->invisibleClass().'"'
			.' value="'.$this->text.'" '.$this->disabledMarker().'/>';
	}
}